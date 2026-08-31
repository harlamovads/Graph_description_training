import api from '../utils/api';

const practiceService = {
  // Start (or resume, if one's already in progress) a practice session for one sentence.
  start: async (submissionId, sentenceIndex) => {
    const response = await api.post('/practice/start', {
      submission_id: submissionId,
      sentence_index: sentenceIndex
    });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/practice/${sessionId}`);
    return response.data;
  },

  submitRound: async (sessionId, text) => {
    const response = await api.post(`/practice/${sessionId}/submit`, { text });
    return response.data;
  },

  stop: async (sessionId) => {
    const response = await api.post(`/practice/${sessionId}/stop`);
    return response.data;
  },

  // Teacher: flag a sentence in a submission for the student to practice.
  assign: async (submissionId, sentenceIndex) => {
    const response = await api.post('/practice/assign', {
      submission_id: submissionId,
      sentence_index: sentenceIndex
    });
    return response.data;
  },

  // Student: sentences assigned by a teacher that haven't been started yet.
  getAssignments: async () => {
    const response = await api.get('/practice/assignments');
    return response.data;
  },

  // Teacher: all practice sessions belonging to their students.
  getTeacherSessions: async () => {
    const response = await api.get('/practice/teacher');
    return response.data;
  },

  // Teacher: full round-by-round detail of one session.
  getSessionReview: async (sessionId) => {
    const response = await api.get(`/practice/${sessionId}/review`);
    return response.data;
  }
};

export default practiceService;
