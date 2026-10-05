import React, { useState } from 'react';
import { Box, Dialog, DialogContent, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ZoomInIcon from '@mui/icons-material/ZoomIn';

/**
 * A task's chart/graph image. Replaces the `CardMedia component="img"` this app used to use
 * everywhere: that applies `object-fit: cover`, which crops a fixed-height box to fill it -
 * fine for decorative photos, wrong for the charts students are asked to describe, where a
 * cropped axis or legend loses the actual content. Here the image is always contained (whole
 * thing visible, letterboxed if need be) and clicking it opens a full-size view.
 *
 * Props:
 *  - src: image url (renders nothing when absent)
 *  - alt: alt text
 *  - maxHeight: cap for the inline thumbnail (default 220)
 */
const TaskImage = ({ src, alt = '', maxHeight = 220 }) => {
  const [open, setOpen] = useState(false);
  // In the enlarged view, toggles between fit-to-viewport and the image's natural size
  // (scrollable) - dense charts can still be unreadable when squeezed into 90vh.
  const [actualSize, setActualSize] = useState(false);

  if (!src) return null;

  const close = () => {
    setOpen(false);
    setActualSize(false);
  };

  return (
    <>
      <Box
        role="button"
        tabIndex={0}
        aria-label={alt ? `Enlarge image: ${alt}` : 'Enlarge image'}
        onClick={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setOpen(true);
          }
        }}
        sx={{
          position: 'relative',
          cursor: 'zoom-in',
          backgroundColor: '#fafafa',
          borderRadius: 1,
          overflow: 'hidden',
          '&:hover .zoom-hint': { opacity: 1 }
        }}
      >
        <Box
          component="img"
          src={src}
          alt={alt}
          sx={{ display: 'block', width: '100%', maxHeight, objectFit: 'contain' }}
        />
        <Box
          className="zoom-hint"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            opacity: 0,
            transition: 'opacity 0.15s',
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            color: '#fff',
            borderRadius: '50%',
            p: 0.5,
            display: 'flex'
          }}
        >
          <ZoomInIcon fontSize="small" />
        </Box>
      </Box>

      <Dialog
        open={open}
        onClose={close}
        maxWidth={false}
        PaperProps={{ sx: { backgroundColor: 'transparent', boxShadow: 'none', m: 1 } }}
      >
        <DialogContent sx={{ p: 0, position: 'relative', overflow: 'auto' }}>
          <IconButton
            onClick={close}
            aria-label="Close"
            sx={{
              position: 'fixed',
              top: 16,
              right: 16,
              zIndex: 1,
              backgroundColor: 'rgba(0, 0, 0, 0.55)',
              color: '#fff',
              '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.75)' }
            }}
          >
            <CloseIcon />
          </IconButton>
          <Box
            component="img"
            src={src}
            alt={alt}
            onClick={() => setActualSize((v) => !v)}
            sx={{
              display: 'block',
              backgroundColor: '#fff',
              cursor: actualSize ? 'zoom-out' : 'zoom-in',
              ...(actualSize
                ? { maxWidth: 'none', maxHeight: 'none' }
                : { maxWidth: '95vw', maxHeight: '90vh', objectFit: 'contain' })
            }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default TaskImage;
