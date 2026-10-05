from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Experiment participation agreement, shown to students at registration. Nullable on
    # purpose: NULL means "never asked" (teachers, and anyone who signed up before this
    # existed), True/False is an explicit answer. So the analysis filter for usable data is
    # `WHERE experiment_consent IS TRUE` - a declining student still gets a working account,
    # their data just isn't eligible.
    experiment_consent = db.Column(db.Boolean, nullable=True)
    experiment_consent_at = db.Column(db.DateTime, nullable=True)

    # A teacher's permanent, shareable invitation code - one per teacher, reusable by any
    # number of students. Codes used to be single-use rows in `invitations`, so a teacher had
    # to generate a fresh one per student. NULL for students, and for teachers who haven't
    # asked for theirs yet (it's created on first request, see routes/auth.py).
    invitation_code = db.Column(db.String(20), unique=True, nullable=True)
    
    # Background a student fills in from their profile page. All nullable and all optional -
    # these are for interpreting the study's results, not for using the app, so nobody is
    # blocked by leaving them blank. Stored as free-ish text rather than enums so the set of
    # answers can be adjusted without a migration; the frontend offers fixed choices for
    # gender and English level to keep the values consistent enough to group by.
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(32), nullable=True)
    native_language = db.Column(db.String(64), nullable=True)
    english_level = db.Column(db.String(32), nullable=True)

    # Relationships
    tasks_created = db.relationship('Task', backref='creator', lazy='dynamic', 
                                  foreign_keys='Task.creator_id')
    tasks_assigned = db.relationship('TaskAssignment', backref='student', lazy='dynamic')
    submissions = db.relationship('Submission', backref='student', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'experiment_consent': self.experiment_consent,
            'experiment_consent_at': self.experiment_consent_at.isoformat() if self.experiment_consent_at else None,
            'age': self.age,
            'gender': self.gender,
            'native_language': self.native_language,
            'english_level': self.english_level
        }


class Invitation(db.Model):
    """A record of one student joining one teacher's class via an invitation code.

    This is a redemption ledger, not a pool of unused tokens: the shareable code itself lives
    on the teacher (User.invitation_code) and is reusable, so `code` here is just a copy of
    whatever code the student redeemed and is no longer unique across rows. Rows are still
    created with is_used=True and student_id set, which is what every "which students belong
    to this teacher" query joins on (routes/auth.py::get_students, stats_service).
    """
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships. Two FKs to users.id (inviting teacher, redeeming student), so each needs
    # its own foreign_keys hint - otherwise SQLAlchemy can't tell which column a plain
    # `User.join(Invitation)` should join on (it'll silently pick one, which is what made the
    # old "students invited via code" lookup in routes/auth.py::get_students always come back
    # empty - it joined on teacher_id and then filtered for role='student', which a teacher
    # row never matches).
    teacher = db.relationship('User', foreign_keys=[teacher_id])
    student = db.relationship('User', foreign_keys=[student_id])