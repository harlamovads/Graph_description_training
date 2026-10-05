import api from '../utils/api';

const taskService = {
  // Get all tasks for the user
  getTasks: async () => {
    const response = await api.get('/tasks');
    return response.data;
  },
  
  // Get a specific task
  getTask: async (taskId) => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },
  
  // Create a new task
  createTask: async (taskData) => {
    // Use FormData for file uploads
    const formData = new FormData();
    
    for (const key in taskData) {
      if (key === 'image' && taskData[key]) {
        formData.append(key, taskData[key]);
      } else {
        formData.append(key, taskData[key]);
      }
    }
    
    const response = await api.post('/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  },
  
  // Update a task. If the task belongs to another teacher (only possible for shared,
  // "task database" tasks), the backend saves the changes to a copy owned by the caller and
  // returns forked: true - see PUT /api/tasks/<id>.
  updateTask: async (taskId, taskData) => {
    const formData = new FormData();

    for (const key in taskData) {
      // Skip the image unless a new file was actually chosen, so the existing one is kept.
      if (key === 'image' && !taskData[key]) continue;
      formData.append(key, taskData[key]);
    }

    const response = await api.put(`/tasks/${taskId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return response.data;
  },

  // Assign a task to students
  assignTask: async (taskId, studentIds, dueDate) => {
    const response = await api.post(`/tasks/${taskId}/assign`, {
      student_ids: studentIds,
      due_date: dueDate
    });
    
    return response.data;
  },
  
  // Get database tasks
  getDatabaseTasks: async () => {
    const response = await api.get('/tasks/database');
    return response.data;
  }
};

export default taskService;