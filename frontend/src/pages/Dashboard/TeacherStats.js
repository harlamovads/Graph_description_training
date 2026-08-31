import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Divider,
  Card,
  CardContent,
  CardActionArea,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PersonIcon from '@mui/icons-material/Person';

import statsService from '../../services/statsService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const formatSeconds = (seconds) => {
  if (seconds === null || seconds === undefined) return 'N/A';
  const minutes = Math.round(seconds / 60);
  if (minutes < 1) return '<1 min';
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
};

const formatScore = (score) => (score !== null && score !== undefined ? score.toFixed(1) : 'N/A');

const TeacherStats = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  // 'all' or a 'YYYY-MM' string - which month's error-type distribution the two charts show.
  const [selectedMonth, setSelectedMonth] = useState('all');

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const response = await statsService.getStudentsSummary();
        setStudents(response.students || []);
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load student stats');
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  const openStudent = async (studentId) => {
    setSelectedStudentId(studentId);
    setDetailLoading(true);
    try {
      const response = await statsService.getStudentDetail(studentId);
      setDetail(response);
      // Default to the most recent month with any data, so "separated by month" is the
      // first thing shown rather than an all-time blend.
      const months = new Set([
        ...(response.monthly_task_stats || []).map((m) => m.month),
        ...Object.keys(response.practice_sessions?.monthly_error_distribution || {})
      ]);
      const sortedMonths = Array.from(months).sort();
      setSelectedMonth(sortedMonths.length > 0 ? sortedMonths[sortedMonths.length - 1] : 'all');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load student detail');
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading student stats..." />;
  }

  if (error) {
    return <ErrorBox error={error} />;
  }

  const availableMonths = detail
    ? Array.from(new Set([
        ...(detail.monthly_task_stats || []).map((m) => m.month),
        ...Object.keys(detail.practice_sessions?.monthly_error_distribution || {})
      ])).sort()
    : [];

  const taskErrorDistributionForMonth = (month) => {
    if (!detail) return {};
    if (month === 'all') return detail.error_distribution || {};
    return detail.monthly_task_stats.find((m) => m.month === month)?.error_distribution || {};
  };
  const practiceErrorDistributionForMonth = (month) => {
    if (!detail) return {};
    if (month === 'all') return detail.practice_sessions?.error_distribution || {};
    return detail.practice_sessions?.monthly_error_distribution?.[month] || {};
  };

  const taskErrorChartData = Object.entries(taskErrorDistributionForMonth(selectedMonth))
    .map(([type, count]) => ({ type, count }));
  const practiceErrorChartData = Object.entries(practiceErrorDistributionForMonth(selectedMonth))
    .map(([type, count]) => ({ type, count }));

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => (selectedStudentId ? setSelectedStudentId(null) : navigate('/dashboard'))}
          sx={{ mr: 2 }}
        >
          {selectedStudentId ? 'Back to All Students' : 'Back to Dashboard'}
        </Button>
        <Typography variant="h4">Student Stats</Typography>
      </Box>

      {!selectedStudentId && (
        <Grid container spacing={2}>
          {students.length === 0 && (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">No students yet.</Typography>
              </Paper>
            </Grid>
          )}
          {students.map((s) => (
            <Grid item xs={12} sm={6} md={4} key={s.student.id}>
              <Card>
                <CardActionArea onClick={() => openStudent(s.student.id)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <PersonIcon sx={{ mr: 1 }} color="primary" />
                      <Typography variant="h6">{s.student.username}</Typography>
                    </Box>
                    <Divider sx={{ mb: 1 }} />
                    <Typography variant="body2">Tasks completed: {s.tasks_completed} / {s.tasks_assigned}</Typography>
                    <Typography variant="body2">Average score: {formatScore(s.average_score)} / 10</Typography>
                    <Typography variant="body2">
                      Practice sessions: {s.practice_sessions_completed} / {s.practice_sessions_total} completed
                    </Typography>
                    <Typography variant="body2">Time spent: {formatSeconds(s.total_time_spent_seconds)}</Typography>
                    <Chip
                      size="small"
                      label={`${s.total_errors} logged error${s.total_errors === 1 ? '' : 's'}`}
                      color={s.total_errors > 0 ? 'warning' : 'success'}
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {selectedStudentId && (
        detailLoading || !detail ? (
          <LoadingSpinner message="Loading student detail..." />
        ) : (
          <Box>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom>{detail.student.username}</Typography>
              <Typography variant="body2" color="text.secondary">{detail.student.email}</Typography>
            </Paper>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <FormControl size="small" sx={{ minWidth: 160 }}>
                <InputLabel id="month-select-label">Month</InputLabel>
                <Select
                  labelId="month-select-label"
                  label="Month"
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                >
                  <MenuItem value="all">All time</MenuItem>
                  {availableMonths.map((month) => (
                    <MenuItem key={month} value={month}>{month}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Task Error Type Distribution (ERRANT) — {selectedMonth === 'all' ? 'All time' : selectedMonth}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {taskErrorChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={taskErrorChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" angle={-30} textAnchor="end" interval={0} height={80} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#1e88e5" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Typography color="text.secondary">No logged task errors yet.</Typography>
              )}
            </Paper>

            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>Time Spent &amp; Score per Task</Typography>
                  <Divider sx={{ mb: 2 }} />
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Task</TableCell>
                          <TableCell align="right">Score</TableCell>
                          <TableCell align="right">Time Spent</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {detail.time_per_task.map((t) => (
                          <TableRow key={t.submission_id}>
                            <TableCell>
                              {t.task_title}
                              {t.is_resubmission && (
                                <Chip size="small" label={`Resubmission ${t.attempt_number - 1}`} sx={{ ml: 1 }} />
                              )}
                            </TableCell>
                            <TableCell align="right">{formatScore(t.score)}</TableCell>
                            <TableCell align="right">{formatSeconds(t.time_spent_seconds)}</TableCell>
                          </TableRow>
                        ))}
                        {detail.time_per_task.length === 0 && (
                          <TableRow><TableCell colSpan={3}>No completed tasks yet.</TableCell></TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>Practice Sessions</Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Typography variant="body2">
                    Completed: {detail.practice_sessions.total_completed} (stopped early: {detail.practice_sessions.total_stopped})
                  </Typography>
                  <Typography variant="body2">
                    Sentences practiced: {detail.practice_sessions.total_sentences_completed}
                  </Typography>
                  <Typography variant="body2">
                    Total time: {formatSeconds(detail.practice_sessions.total_time_spent_seconds)}
                  </Typography>

                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                    Error Type Distribution (practice) — {selectedMonth === 'all' ? 'All time' : selectedMonth}
                  </Typography>
                  {practiceErrorChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={practiceErrorChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="type" angle={-30} textAnchor="end" interval={0} height={60} />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#64b5f6" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <Typography color="text.secondary">No practice sessions yet.</Typography>
                  )}
                </Paper>
              </Grid>
            </Grid>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Monthly Progress</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Month</TableCell>
                      <TableCell align="right">Submissions</TableCell>
                      <TableCell align="right">Average Score</TableCell>
                      <TableCell align="right">Time Spent</TableCell>
                      <TableCell align="right">Errors</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detail.monthly_task_stats.map((m) => (
                      <TableRow key={m.month}>
                        <TableCell>{m.month}</TableCell>
                        <TableCell align="right">{m.submissions_count}</TableCell>
                        <TableCell align="right">{formatScore(m.average_score)}</TableCell>
                        <TableCell align="right">{formatSeconds(m.total_time_spent_seconds)}</TableCell>
                        <TableCell align="right">{m.total_errors}</TableCell>
                      </TableRow>
                    ))}
                    {detail.monthly_task_stats.length === 0 && (
                      <TableRow><TableCell colSpan={5}>No submissions yet.</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Box>
        )
      )}
    </Box>
  );
};

export default TeacherStats;
