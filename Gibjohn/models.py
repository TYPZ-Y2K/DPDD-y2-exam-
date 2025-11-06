from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

# --- Data models ---
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)  # auto-incrementing ID
    role = db.Column(db.String(16), nullable=False)  # use enum-like validation in code
    email = db.Column(db.String(120), unique=True, nullable=False)  # unique email address
    password_hash = db.Column(db.Text, nullable=False)  # hashed password
    full_name = db.Column(db.String(120))
    dob = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # account creation timestamp
    last_login = db.Column(db.DateTime)
    def get_id(self):
        return str(self.user_id)

    def set_password(self, pw):  # hash and store password
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):  # verify password
        return check_password_hash(self.password_hash, pw)

class Class(db.Model):
    __tablename__ = 'classes'
    class_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))  # class title
    subject = db.Column(db.String(80))
    year_group = db.Column(db.Integer)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # tutor user ID
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ClassEnrollment(db.Model):
    __tablename__ = 'class_enrollments'
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # enrollment timestamp

class Resources(db.Model):
    __tablename__ = 'resources'
    resource_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(16), nullable=False, default="misc")
    type = db.Column(db.String(16), nullable=False, default="file")  # 'file' | 'link'
    description = db.Column(db.Text)
    url = db.Column(db.String(255))  # for links
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    path = db.Column(db.String(255))
    mime = db.Column(db.String(64))
    size = db.Column(db.Integer)


class Assignment(db.Model):
    __tablename__ = 'assignments'
    assignment_id = db.Column(db.Integer, primary_key=True)
    resource_id   = db.Column(db.Integer, db.ForeignKey('resources.resource_id'), nullable=False)
    class_id      = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    title         = db.Column(db.String(120), nullable=False)
    due_date      = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

class Submission(db.Model):
    __tablename__ = 'submissions'
    submission_id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.assignment_id'), nullable=False)  # linked assignment
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(16), nullable=False)  # e.g. submitted, graded
    score = db.Column(db.Float)  # optional score
    feedback = db.Column(db.Text)  # optional feedback
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # submission timestamp

class Progress(db.Model):
    __tablename__ = 'progress'
    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    best_score = db.Column(db.Float)  # best score achieved
    attempts = db.Column(db.Integer, default=0)  # number of attempts made
    last_attempted = db.Column(db.DateTime)

class Reward(db.Model):
    __tablename__ = 'rewards'
    reward_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)  # reward title
    description = db.Column(db.Text)  # reward description
    criteria = db.Column(db.Integer, nullable=False)  # e.g. points needed


class UserReward(db.Model):
    __tablename__ = 'user_rewards'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False)  # composite key
    reward_id = db.Column(db.Integer, db.ForeignKey('rewards.reward_id'), primary_key=True, nullable=False)  # composite key
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # when earned

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)  # e.g. "Completed Quiz 1"
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # when action occurred

