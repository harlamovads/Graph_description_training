# models/sentence.py
from . import db
import json

class Sentence(db.Model):
    __tablename__ = 'sentences'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)  # Changed from content to text to match your data
    error_tags = db.Column(db.Text)  # JSON string with error spans and tags
    
    def get_error_tags(self):
        if self.error_tags:
            return json.loads(self.error_tags)
        return []
    
    def set_error_tags(self, tags):
        self.error_tags = json.dumps(tags)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'error_tags': self.get_error_tags()
        }