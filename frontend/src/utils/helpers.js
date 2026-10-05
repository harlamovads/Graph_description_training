// Task due dates come from the student's own TaskAssignment row, merged into the task payload
// by backend/routes/tasks.py. They're null when the teacher didn't set one, so every caller
// has to handle that.

export const formatDueDate = (dueDate) => {
  if (!dueDate) return null;
  const date = new Date(dueDate);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
};

// Compared against the end of the due day, so a task due today isn't flagged overdue while
// the student still has the rest of the day to hand it in.
export const isOverdue = (dueDate) => {
  if (!dueDate) return false;
  const date = new Date(dueDate);
  if (Number.isNaN(date.getTime())) return false;
  date.setHours(23, 59, 59, 999);
  return date.getTime() < Date.now();
};

// Submissions are stored as the rich-text editor's HTML, but teacher annotations address the
// text by character offset. Both the annotating view and the student's read-only view must
// derive exactly the same plain text from that HTML, or an annotation would point at different
// words in each - hence one shared function rather than per-page markup handling.
export const htmlToPlainText = (html) => {
  if (!html) return '';
  const withBreaks = String(html)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|h[1-6]|li|blockquote)\s*>/gi, '\n\n');
  const el = document.createElement('div');
  el.innerHTML = withBreaks;
  const text = el.textContent || '';
  return text
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
};
