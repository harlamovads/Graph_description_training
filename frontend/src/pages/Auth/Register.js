import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Avatar,
  Button,
  TextField,
  Link,
  Grid,
  Box,
  Typography,
  Container,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { register } from '../../redux/actions/authActions';
import LoadingSpinner from '../../components/common/LoadingSpinner';

// Placeholder - replace with the real experiment participation agreement text.
const AGREEMENT_TEXT = `Информированное согласие

В этом исследовании изучается эффективность двух форматов домашней работы во время обучения академическому письму на английском языке: 1) стандартный вариант по учебным пособиям и 2) с использованием программы с автоматической обратной связью.
Ваша учебная группа участвует в исследовании как контрольная или как экспериментальная. В обоих случаях вы осваиваете описание графика в рамках обязательного курса английского языка.
Что вам предстоит сделать:
•	в начале курса выполнить входное тестирование: написать описание графика в программе;
•	пройти обучение в формате вашей группы;
•	в конце курса выполнить финальное тестирование в том же формате;
•	сразу после финального тестирования заполнить анкету с открытыми вопросами о вашем опыте обучения (около 15 минут);
•	по желанию заполнить дополнительный полностью анонимный опрос впечатлений о курсе.

Какие данные собираются: тексты и ответы, которые вы создаёте в системе, и автоматическая разметка языковых ошибок в них; ответы на короткий опросник (возраст, пол, родной язык, уровень английского языка); ваши ответы на анкету; балл за итоговый экзамен курса и текст описания графика из вашей экзаменационной работы.
Добровольность. Освоение курса является частью учебного процесса и обязательно для всех студентов. Добровольным является именно использование ваших данных в научном исследовании. Вы можете отказаться от участия в исследовании или отозвать согласие в любой момент, в том числе после того, как данные уже собраны, написав по адресу explinguistics@gmail.com. В этом случае ваши данные будут исключены из анализа. Отказ никак не влияет на вашу оценку по курсу и на условия обучения. Если вам некомфортно отвечать на какой-либо вопрос, вы можете его пропустить.
Преподаватели курса не получают доступа к исследовательскому массиву и не знают, кто дал согласие на участие. Каждому участнику присваивается индивидуальный код; таблица соответствия кода и учётной записи хранится отдельно от данных.
Результаты публикуются только в обобщённом виде, без возможности установить, к кому относятся те или иные данные. Обезличенные предложения с разметкой языковых ошибок могут быть опубликованы в открытом доступе как исследовательские данные. Личная информация и результаты анкетирования в открытом доступе не публикуются.
Автоматическая обратная связь может содержать ошибки: система не всегда верно определяет и классифицирует ошибку. Её рекомендации не являются оценкой и при несогласии вы можете обратиться к преподавателю.

Исследование не предполагает физических или психологических нагрузок сверх обычных учебных. Вы получите индивидуальную обратную связь по результатам входного и финального тестирования. Если ваша группа является контрольной, вы получите доступ к системе после завершения эксперимента.
Участие в эксперименте является абсолютно добровольным. Вы можете прервать участие в эксперименте в любой момент по любой причине. 
Вся собранная информация будет анонимизирована. Ваши персональные данные не будут упомянуты где-либо. Все результаты будут представляться только в общем массиве, а не индивидуально. По итогам исследования мы планируем опубликовать результаты в реферируемых журналах.
Нажимая на кнопку I AGREE, Вы подтверждаете, что действуете без принуждения, по собственной воле и в своих интересах.
`;

const Register = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, user, loading, error } = useSelector(state => state.auth);
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'student',
    invitation_code: ''
  });

  // null = not answered yet (blocks sign-up), true/false = an explicit choice. Declining is
  // a valid answer: the account still works, the choice is just recorded so the team can
  // exclude that student's data at analysis time.
  const [experimentConsent, setExperimentConsent] = useState(null);

  const { username, email, password, role, invitation_code } = formData;
  const needsConsent = role === 'student';
  const consentMissing = needsConsent && experimentConsent === null;
  
  useEffect(() => {
  if (isAuthenticated && user) {
    if (user.role === 'teacher') {
      navigate('/dashboard');
    } else {
      navigate('/student-dashboard');
    }
  }
}, [isAuthenticated, user, navigate]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    // Switching away from the student role clears any answer, so a teacher never submits one.
    if (name === 'role' && value !== 'student') {
      setExperimentConsent(null);
    }
    setFormData({ ...formData, [name]: value });
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // The button is disabled in this state, but the form can also be submitted with Enter.
    if (consentMissing) return;

    const payload = { ...formData };
    if (needsConsent) {
      payload.experiment_consent = experimentConsent;
    }
    dispatch(register(payload));
  };
  
  if (loading) {
    return <LoadingSpinner message="Registering..." />;
  }
  
  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
          <PersonAddIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          Sign up
        </Typography>
        <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 3 }}>
          {error && (
            <Typography color="error" align="center" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                value={email}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={password}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="role-label">Role</InputLabel>
                <Select
                  labelId="role-label"
                  id="role"
                  name="role"
                  value={role}
                  label="Role"
                  onChange={handleChange}
                >
                  <MenuItem value="student">Student</MenuItem>
                  <MenuItem value="teacher">Teacher</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {role === 'student' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  name="invitation_code"
                  label="Invitation Code (Optional)"
                  id="invitation_code"
                  value={invitation_code}
                  onChange={handleChange}
                  helperText="Enter the invitation code provided by your teacher to be automatically assigned to their class"
                />
              </Grid>
            )}

            {/* Experiment participation agreement - students only. */}
            {needsConsent && (
              <Grid item xs={12}>
                <Accordion defaultExpanded id="agreement-accordion">
                  <AccordionSummary expandIcon={<ExpandMoreIcon />} id="agreement-header">
                    <Typography variant="subtitle2">
                      Experiment participation agreement
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ maxHeight: 200, overflowY: 'auto', pr: 1 }}>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ whiteSpace: 'pre-line' }}
                      >
                        {AGREEMENT_TEXT}
                      </Typography>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                <Box sx={{ display: 'flex', gap: 1, mt: 1.5 }}>
                  <Button
                    fullWidth
                    id="agree-button"
                    variant={experimentConsent === true ? 'contained' : 'outlined'}
                    onClick={() => setExperimentConsent(true)}
                  >
                    I agree
                  </Button>
                  <Button
                    fullWidth
                    id="disagree-button"
                    variant={experimentConsent === false ? 'contained' : 'outlined'}
                    onClick={() => setExperimentConsent(false)}
                  >
                    I do not agree
                  </Button>
                </Box>

                {/* Sits directly under the two buttons, in light grey: this is the wording the
                    university requires alongside the consent choice itself. */}
                <Typography
                  variant="caption"
                  sx={{ display: 'block', mt: 1, color: 'text.disabled', lineHeight: 1.5 }}
                >
                  Я подтверждаю, что лично ознакомился с Положением об обработке персональных
                  данных НИУ ВШЭ, вправе предоставлять свои персональные данные и давать согласие
                  на их обработку.
                </Typography>

                <Box sx={{ mt: 1 }}>
                  {experimentConsent === null ? (
                    <Typography variant="caption" color="text.secondary">
                      Choose one option to continue. You can sign up either way - your choice
                      only decides whether your data is used in the study.
                    </Typography>
                  ) : (
                    <Chip
                      size="small"
                      label={
                        experimentConsent
                          ? 'You agreed to take part'
                          : 'You chose not to take part'
                      }
                      color={experimentConsent ? 'success' : 'default'}
                      variant="outlined"
                    />
                  )}
                </Box>
              </Grid>
            )}
          </Grid>
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={consentMissing}
            sx={{ mt: 3, mb: 2 }}
          >
            Sign Up
          </Button>
          <Grid container justifyContent="flex-end">
            <Grid item>
              <Link component={RouterLink} to="/login" variant="body2">
                Already have an account? Sign in
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Container>
  );
};

export default Register;
