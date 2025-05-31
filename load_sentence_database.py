# load_sentence_database.py
import json
import os
from app import create_app
from backend.models import db
from backend.models.sentence import Sentence

def discover_tags_in_file(jsonl_file_path='sentencewise_full.jsonl', sample_size=1000):
    """Discover what second_level_tag values are actually in the file"""
    print(f"Discovering tags in {jsonl_file_path}...")
    
    all_second_level_tags = set()
    all_native_tags = set()
    all_first_level_tags = set()
    lines_processed = 0
    
    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line_num > sample_size:
                    break
                    
                try:
                    line = line.strip()
                    if not line:
                        continue
                        
                    data = json.loads(line)
                    tags = data.get('tags', [])
                    
                    for tag in tags:
                        if tag.get('second_level_tag'):
                            all_second_level_tags.add(tag['second_level_tag'])
                        if tag.get('native_tag'):
                            all_native_tags.add(tag['native_tag'])
                        if tag.get('first_level_tag'):
                            all_first_level_tags.add(tag['first_level_tag'])
                    
                    lines_processed += 1
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue
        
        print(f"Analyzed {lines_processed} lines from the file")
        print(f"Found second_level_tags: {sorted(all_second_level_tags)}")
        print(f"Found native_tags: {sorted(all_native_tags)}")
        print(f"Found first_level_tags: {sorted(all_first_level_tags)}")
        
        return sorted(all_second_level_tags), sorted(all_native_tags), sorted(all_first_level_tags)
        
    except FileNotFoundError:
        print(f"Error: {jsonl_file_path} not found")
        return [], [], []

def load_sentence_database(jsonl_file_path='sentencewise_full.jsonl'):
    """Load sentence database from JSONL file with proper tag handling"""
    print(f"Loading sentence database from: {jsonl_file_path}")
    
    # First, discover what tags are actually in the file
    second_level_tags, native_tags, first_level_tags = discover_tags_in_file(jsonl_file_path, 5000)
    
    if not second_level_tags:
        print("No tags discovered. Please check the file format.")
        return
    
    print(f"\nDiscovered {len(second_level_tags)} unique second_level_tags:")
    for tag in second_level_tags:
        print(f"  - {tag}")
    
    # Ask user which tags to include (or use all)
    print("\nDo you want to:")
    print("1. Include ALL discovered second_level_tags")
    print("2. Include only specific tags")
    choice = input("Enter choice (1 or 2, default 1): ").strip() or "1"
    
    if choice == "2":
        print("Enter the tags you want to include (comma-separated):")
        user_tags = input("Tags: ").strip()
        if user_tags:
            valid_tags = set(tag.strip() for tag in user_tags.split(','))
        else:
            valid_tags = set(second_level_tags)
    else:
        valid_tags = set(second_level_tags)
    
    print(f"\nUsing tags: {sorted(valid_tags)}")
    
    app = create_app()
    
    with app.app_context():
        # Check if data already loaded
        existing_count = Sentence.query.count()
        if existing_count > 0:
            print(f"Sentence database already loaded with {existing_count} sentences")
            response = input("Do you want to reload the database? (y/N): ")
            if response.lower() != 'y':
                return
            
            # Clear existing data
            print("Clearing existing sentence database...")
            Sentence.query.delete()
            db.session.commit()
            print("Existing data cleared")
        
        # Load JSONL file
        try:
            print(f"Loading sentences from {jsonl_file_path}...")
            lines_processed = 0
            lines_with_errors = 0
            tag_distribution = {}
            
            with open(jsonl_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:  # Skip empty lines
                            continue
                            
                        data = json.loads(line)
                        text = data.get('text', '').strip()
                        tags = data.get('tags', [])
                        
                        if not text or not tags:
                            continue
                        
                        # Filter for valid tags
                        valid_sentence_tags = []
                        sentence_error_types = set()
                        
                        for tag in tags:
                            # Check if tag has required fields
                            error_span = tag.get('error_span', '').strip()
                            correction = tag.get('correction', '').strip()
                            second_level = tag.get('second_level_tag', '').strip()
                            
                            # Include tag if it has the required fields and valid second_level_tag
                            if error_span and second_level and second_level in valid_tags:
                                sentence_error_types.add(second_level)
                                valid_sentence_tags.append(tag)
                                
                                # Count tag distribution
                                tag_distribution[second_level] = tag_distribution.get(second_level, 0) + 1
                        
                        # Only add sentences that have valid tags
                        if valid_sentence_tags and sentence_error_types:
                            sentence = Sentence(text=text)
                            sentence.set_error_tags(valid_sentence_tags)
                            db.session.add(sentence)
                            lines_with_errors += 1
                        
                        lines_processed += 1
                        
                        # Progress update and batch commit
                        if line_num % 1000 == 0:
                            db.session.commit()
                            print(f"Processed {line_num} lines, added {lines_with_errors} sentences with valid tags...")
                        
                        # Debug: Print first few entries
                        if line_num <= 5:
                            print(f"Line {line_num}: text='{text[:50]}...', error types={list(sentence_error_types)}")
                        
                    except json.JSONDecodeError as e:
                        if line_num <= 10:  # Only show first few JSON errors
                            print(f"JSON decode error on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        if line_num <= 10:  # Only show first few general errors
                            print(f"Error processing line {line_num}: {e}")
                        continue
            
            # Final commit
            db.session.commit()
            print(f"\nSuccessfully loaded sentence database:")
            print(f"- Total lines processed: {lines_processed}")
            print(f"- Sentences with valid tags added: {lines_with_errors}")
            
            # Verify the load
            final_count = Sentence.query.count()
            print(f"- Final database count: {final_count}")
            
            # Show tag distribution
            print(f"\n- Tag distribution across all loaded sentences:")
            for tag, count in sorted(tag_distribution.items()):
                print(f"  {tag}: {count}")
            
            # Verify with a sample from database
            if final_count > 0:
                print(f"\n- Verification: Checking sample from database...")
                sample_sentences = Sentence.query.limit(10).all()
                for i, sentence in enumerate(sample_sentences, 1):
                    tags = sentence.get_error_tags()
                    error_types = set()
                    for tag in tags:
                        if tag.get('second_level_tag'):
                            error_types.add(tag['second_level_tag'])
                    print(f"  Sample {i}: {sentence.text[:50]}... -> {list(error_types)}")
                    
                    if i >= 3:  # Show first 3 samples
                        break
            
        except FileNotFoundError:
            print(f"Error: {jsonl_file_path} not found in {os.getcwd()}")
            print("Please ensure the sentencewise_full.jsonl file is in the project root directory")
        except Exception as e:
            print(f"Error loading sentence database: {e}")
            db.session.rollback()

def clear_sentence_database():
    """Clear the sentence database"""
    app = create_app()
    
    with app.app_context():
        count = Sentence.query.count()
        if count == 0:
            print("Sentence database is already empty")
            return
            
        response = input(f"Are you sure you want to delete {count} sentences? (y/N): ")
        if response.lower() == 'y':
            Sentence.query.delete()
            db.session.commit()
            print(f"Deleted {count} sentences from database")
        else:
            print("Operation cancelled")

def show_database_stats():
    """Show statistics about the sentence database"""
    app = create_app()
    
    with app.app_context():
        total_sentences = Sentence.query.count()
        print(f"Total sentences in database: {total_sentences}")
        
        if total_sentences > 0:
            # Get tag distribution
            sample_sentences = Sentence.query.limit(min(1000, total_sentences)).all()
            tag_counts = {}
            
            for sentence in sample_sentences:
                error_tags = sentence.get_error_tags()
                for tag in error_tags:
                    second_level = tag.get('second_level_tag')
                    if second_level:
                        tag_counts[second_level] = tag_counts.get(second_level, 0) + 1
            
            print(f"\nTag distribution in sample of {len(sample_sentences)} sentences:")
            for tag, count in sorted(tag_counts.items()):
                print(f"  {tag}: {count}")
            
            # Sample some sentences
            sample_sentences = Sentence.query.limit(5).all()
            print(f"\nSample sentences:")
            for i, sentence in enumerate(sample_sentences, 1):
                error_tags = sentence.get_error_tags()
                error_types = set()
                for tag in error_tags:
                    if tag.get('second_level_tag'):
                        error_types.add(tag['second_level_tag'])
                
                print(f"{i}. {sentence.text[:80]}...")
                print(f"   Error types: {', '.join(error_types)}")
                print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "discover":
            file_path = sys.argv[2] if len(sys.argv) > 2 else 'sentencewise_full.jsonl'
            discover_tags_in_file(file_path)
        elif command == "load":
            file_path = sys.argv[2] if len(sys.argv) > 2 else 'sentencewise_full.jsonl'
            load_sentence_database(file_path)
        elif command == "clear":
            clear_sentence_database()
        elif command == "stats":
            show_database_stats()
        else:
            print("Unknown command. Use: discover, load, clear, or stats")
    else:
        print("Usage:")
        print("  python load_sentence_database.py discover [file_path]")
        print("  python load_sentence_database.py load [file_path]")
        print("  python load_sentence_database.py clear")
        print("  python load_sentence_database.py stats")