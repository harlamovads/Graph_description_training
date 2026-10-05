import api from '../utils/api';

const submissionService = {
  // Create a new submission
  createSubmission: async (submissionData) => {
    const response = await api.post('/submissions', submissionData);
    return response.data;
  },
  
  // Get a specific submission
  getSubmission: async (submissionId) => {
    const response = await api.get(`/submissions/${submissionId}`);
    return response.data;
  },
  
  // Get submissions for a teacher
  getTeacherSubmissions: async () => {
    const response = await api.get('/submissions/teacher');
    return response.data;
  },
  
  // Get submissions for a student
  getStudentSubmissions: async () => {
    const response = await api.get('/submissions/student');
    return response.data;
  },
  
  // Review a submission (teacher only). `corrections` and `score` are optional:
  // corrections: { [sentenceId]: "teacher's corrected text" }, score: number 0-10
  reviewSubmission: async (submissionId, feedback, corrections, score) => {
    const response = await api.post(`/submissions/${submissionId}/review`, {
      feedback,
      corrections,
      score
    });

    return response.data;
  },

  // Teacher annotations on the student's text. Saved on their own, independently of the review,
  // so a teacher can annotate while reading and keep annotating after the review is sent.
  saveAnnotations: async (submissionId, annotations) => {
    const response = await api.put(`/submissions/${submissionId}/annotations`, { annotations });
    return response.data;
  }
};

export default submissionService;