import React from 'react';
import { Box, Typography, Tooltip, Paper } from '@mui/material';

// Color by the coarse ERRANT operation (see backend/services/errant_service.py):
// R = replacement, M = missing/insertion, U = unnecessary/deletion.
const CATEGORY_COLORS = {
  R: { bg: '#fff3e0', border: '#fb8c00' }, // replaced
  M: { bg: '#e3f2fd', border: '#1e88e5' }, // missing (needs an insertion)
  U: { bg: '#ffebee', border: '#e53935' }, // unnecessary (should be deleted)
  OTHER: { bg: '#f5f5f5', border: '#9e9e9e' }
};

// A single, less-aggressive tone used everywhere in practice-session mode (see
// GrammarDiffView's `gentleHighlight` prop) instead of the red/orange category colors above -
// those read as too harsh for a guided practice exercise.
const GENTLE_COLOR = { bg: '#e3f2fd', border: '#64b5f6' };

/**
 * Renders `original` with each ERRANT edit's span highlighted (color by edit category),
 * a tooltip showing the ERRANT type + suggested replacement, and the corrected text below.
 *
 * This replaces the old server-built `html_output` blob: edits are the real diff between
 * `original` and `corrected` (see errant_service.compute_edits), so what's highlighted here
 * always matches what was actually changed - by the neural network, or by a teacher's edit.
 *
 * Props:
 *  - original: string
 *  - corrected: string (the NN's correction, or a teacher's edited version)
 *  - edits: array of { errant_type, category, original_text, corrected_text, start_char, end_char }
 *  - showCorrected: whether to render the corrected text block below (default true)
 *  - gentleHighlight: use a single light-blue tone for every edit instead of the red/orange/
 *    blue category colors - used in practice-session mode (default false)
 *  - suggestionsAboveSpan: show each edit's suggested correction as an always-visible label
 *    above the highlighted span, instead of only on hover (default false) - used for a
 *    practice session's initial pass over a sentence, so the student has to read the
 *    suggestion rather than just copy the separate "Corrected" block below
 */
const GrammarDiffView = ({
  original, corrected, edits = [], showCorrected = true, gentleHighlight = false, suggestionsAboveSpan = false
}) => {
  const sorted = [...edits].sort((a, b) => a.start_char - b.start_char);

  const segments = [];
  let cursor = 0;
  sorted.forEach((edit, idx) => {
    if (edit.start_char > cursor) {
      segments.push({ type: 'text', text: original.slice(cursor, edit.start_char) });
    }
    segments.push({ type: 'edit', edit, key: idx });
    cursor = Math.max(cursor, edit.end_char);
  });
  if (cursor < original.length) {
    segments.push({ type: 'text', text: original.slice(cursor) });
  }

  return (
    <Box>
      <Paper variant="outlined" sx={{ p: 2, pt: suggestionsAboveSpan ? 4 : 2, backgroundColor: '#fff' }}>
        <Typography variant="body1" component="div" sx={{ lineHeight: suggestionsAboveSpan ? 3 : 2 }}>
          {segments.map((seg, i) => {
            if (seg.type === 'text') {
              return <React.Fragment key={i}>{seg.text}</React.Fragment>;
            }
            const colors = gentleHighlight
              ? GENTLE_COLOR
              : (CATEGORY_COLORS[seg.edit.category] || CATEGORY_COLORS.OTHER);
            const isInsertion = seg.edit.original_text === '';
            const label = isInsertion
              ? `${seg.edit.errant_type}: insert "${seg.edit.corrected_text}"`
              : seg.edit.corrected_text
                ? `${seg.edit.errant_type}: → "${seg.edit.corrected_text}"`
                : `${seg.edit.errant_type}: remove`;

            const spanBox = (
              <Box
                component="span"
                sx={{
                  backgroundColor: colors.bg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '3px',
                  padding: isInsertion ? '0 2px' : '0 3px',
                  margin: '0 1px',
                  cursor: suggestionsAboveSpan ? 'default' : 'help'
                }}
              >
                {isInsertion ? '‸' : seg.edit.original_text}
              </Box>
            );

            if (suggestionsAboveSpan) {
              // A deletion has no replacement text, and the word "remove" doesn't read as an
              // instruction at a glance. Show the span itself struck through instead, which says
              // "this goes away" without having to be read.
              const isDeletion = !seg.edit.corrected_text;
              return (
                <Box key={i} component="span" sx={{ position: 'relative', display: 'inline-block' }}>
                  <Box
                    component="span"
                    sx={{
                      position: 'absolute',
                      top: '-1.5em',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      whiteSpace: 'nowrap',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: '#2e7d32',
                      backgroundColor: '#e8f5e9',
                      border: '1px solid #a5d6a7',
                      borderRadius: '3px',
                      padding: '0 4px',
                      lineHeight: 1.5,
                      // Struck through in a neutral grey rather than red: red spans were
                      // explicitly too aggressive for practice mode, and the strikethrough
                      // already carries the meaning on its own.
                      ...(isDeletion && {
                        textDecoration: 'line-through',
                        color: '#546e7a',
                        backgroundColor: '#eceff1',
                        borderColor: '#b0bec5'
                      })
                    }}
                  >
                    {isDeletion ? seg.edit.original_text : seg.edit.corrected_text}
                  </Box>
                  {spanBox}
                </Box>
              );
            }

            return (
              <Tooltip key={i} title={label} arrow>
                {spanBox}
              </Tooltip>
            );
          })}
        </Typography>
      </Paper>

      {showCorrected && corrected && corrected !== original && (
        <Paper variant="outlined" sx={{ p: 2, mt: 1, backgroundColor: '#f0fff4', borderColor: '#c3e6cb' }}>
          <Typography variant="caption" color="text.secondary">Corrected</Typography>
          <Typography variant="body1">{corrected}</Typography>
        </Paper>
      )}

      {edits.length === 0 && (
        <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
          ✅ No errors detected
        </Typography>
      )}
    </Box>
  );
};

export default GrammarDiffView;
