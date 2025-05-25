import React, { useState, useEffect } from 'react';
import { EditorState, ContentState, convertToRaw } from 'draft-js';
import { Editor } from 'react-draft-wysiwyg';
import draftToHtml from 'draftjs-to-html';
import htmlToDraft from 'html-to-draftjs';
import 'react-draft-wysiwyg/dist/react-draft-wysiwyg.css';
import { Box, Paper } from '@mui/material';

const RichTextEditor = ({ initialValue = '', onChange, readOnly = false }) => {
  const [editorState, setEditorState] = useState(EditorState.createEmpty());

  useEffect(() => {
    if (initialValue) {
      const blocksFromHtml = htmlToDraft(initialValue);
      const { contentBlocks, entityMap } = blocksFromHtml;
      const contentState = ContentState.createFromBlockArray(contentBlocks, entityMap);
      setEditorState(EditorState.createWithContent(contentState));
    }
  }, [initialValue]);

  const handleEditorChange = (state) => {
    setEditorState(state);
    
    if (onChange) {
      const htmlContent = draftToHtml(convertToRaw(state.getCurrentContent()));
      onChange(htmlContent);
    }
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Paper
        sx={{
          minHeight: 200,
          border: '1px solid #ddd',
          padding: 1
        }}
      >
        <Editor
          editorState={editorState}
          onEditorStateChange={handleEditorChange}
          readOnly={readOnly}
          toolbar={{
            options: ['inline', 'blockType', 'list', 'textAlign', 'link', 'history'],
            inline: {
              options: ['bold', 'italic', 'underline'],
            },
          }}
          editorStyle={{
            minHeight: '180px',
            padding: '0 10px',
          }}
        />
      </Paper>
    </Box>
  );
};

export default RichTextEditor;