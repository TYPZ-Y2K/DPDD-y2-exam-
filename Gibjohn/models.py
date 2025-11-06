from datetime import datetime, timezone
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, func, Enum as SAEnum

db = SQLAlchemy()

# ----- Helpers -----
UTC_NOW = lambda: datetime.now(timezone.utc)

# ----- User -----
class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id      = db.Column(db.Integer, primary_key=True)
    role         = db.Column(db.String(16), nullable=False)   # "student" | "tutor" | "guardian"
    email        = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash= db.Column(db.Text, nullable=False)
    full_name    = db.Column(db.String(120))
    dob          = db.Column(db.Date)
    created_at   = db.Column(db.DateTime, nullable=False, default=UTC_NOW)
    last_login   = db.Column(db.DateTime)

    # Relationships
    classes_taught = db.relationship(
        "Class",
        back_populates="tutor",
        cascade="all, delete-orphan",
        foreign_keys="Class.tutor_id",
    )
    resources = db.relationship(
        "Resources",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    enrollments = db.relationship(
        "ClassEnrollment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    submissions = db.relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    progress    = db.relationship("Progress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity    = db.relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    user_rewards= db.relationship("UserReward", back_populates="user", cascade="all, delete-orphan")

    def get_id(self):
        return str(self.user_id)

    def set_password(self, pw: str) -> None:
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f"<User {self.user_id} {self.email} ({self.role})>"

# ----- Class (teaching group) -----
class Class(db.Model):
    __tablename__ = "classes"

    class_id    = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(120), nullable=False)
    subject     = db.Column(db.String(80), nullable=False)
    year_group  = db.Column(db.Integer, nullable=False)
    tutor_id    = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at  = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    tutor = db.relationship("User", back_populates="classes_taught", foreign_keys=[tutor_id])

    # enrollments and students (many-to-many via ClassEnrollment)
    enrollments = db.relationship("ClassEnrollment", back_populates="klass", cascade="all, delete-orphan")
    students = db.relationship(
        "User",
        secondary="class_enrollments",
        primaryjoin="Class.class_id==ClassEnrollment.class_id",
        secondaryjoin="User.user_id==ClassEnrollment.user_id",
        viewonly=True,
    )

    assignments = db.relationship("Assignment", back_populates="class_", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Class {self.class_id} {self.title}>"

# ----- ClassEnrollment (join table) -----
class ClassEnrollment(db.Model):
    __tablename__ = "class_enrollments"

    class_id    = db.Column(db.Integer, db.ForeignKey("classes.class_id"), primary_key=True, nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True, nullable=False)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    klass = db.relationship("Class", back_populates="enrollments")
    user  = db.relationship("User", back_populates="enrollments")

    def __repr__(self):
        return f"<Enroll class={self.class_id} user={self.user_id}>"

# ----- Resources (files/links) -----
class Resources(db.Model):
    __tablename__ = "resources"

    resource_id = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(120), nullable=False)
    subject     = db.Column(db.String(16), nullable=False, default="misc")
    type        = db.Column(db.String(16), nullable=False, default="file")  # 'file' | 'link'
    description = db.Column(db.Text)
    url         = db.Column(db.String(255))          # for links
    owner_id    = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at  = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    # optional file metadata
    path        = db.Column(db.String(255))
    mime        = db.Column(db.String(64))
    size        = db.Column(db.Integer)

    owner = db.relationship("User", back_populates="resources")
    assignments = db.relationship("Assignment", back_populates="resource")  # no delete-orphan: assignment owns FK

    def __repr__(self):
        return f"<Resource {self.resource_id} {self.title} ({self.type})>"

Index("ix_resources_owner_created", Resources.owner_id, Resources.created_at.desc())

# ----- Assignment -----
class Assignment(db.Model):
    __tablename__ = "assignments"

    assignment_id = db.Column(db.Integer, primary_key=True)
    resource_id   = db.Column(db.Integer, db.ForeignKey("resources.resource_id"), nullable=False)
    class_id      = db.Column(db.Integer, db.ForeignKey("classes.class_id"), nullable=False)
    title         = db.Column(db.String(120), nullable=False)
    due_date      = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, nullable=False, default=UTC_NOW)
    updated_at    = db.Column(db.DateTime, nullable=False, default=UTC_NOW, onupdate=UTC_NOW)

    class_   = db.relationship("Class", back_populates="assignments")
    resource = db.relationship("Resources", back_populates="assignments")
    submissions = db.relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assignment {self.assignment_id} {self.title}>"

Index("ix_assignments_class_created", Assignment.class_id, Assignment.created_at.desc())

# ----- Submission -----
class Submission(db.Model):
    __tablename__ = "submissions"

    submission_id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.assignment_id"), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    status        = db.Column(db.String(16), nullable=False)  # 'submitted' | 'graded' | etc
    score         = db.Column(db.Float)
    feedback      = db.Column(db.Text)
    submitted_at  = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    assignment = db.relationship("Assignment", back_populates="submissions")
    user       = db.relationship("User", back_populates="submissions")

    def __repr__(self):
        return f"<Submission {self.submission_id} a={self.assignment_id} u={self.user_id}>"

# ----- Progress (1:1 with User) -----
class Progress(db.Model):
    __tablename__ = "progress"

    progress_id   = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)
    best_score    = db.Column(db.Float)
    attempts      = db.Column(db.Integer, default=0)
    last_attempted= db.Column(db.DateTime)

    user = db.relationship("User", back_populates="progress")

    def __repr__(self):
        return f"<Progress user={self.user_id} best={self.best_score}>"

# ----- Rewards -----
class Reward(db.Model):
    __tablename__ = "rewards"

    reward_id   = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    criteria    = db.Column(db.Integer, nullable=False)  # e.g., points needed

    user_rewards = db.relationship("UserReward", back_populates="reward", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Reward {self.reward_id} {self.title}>"

class UserReward(db.Model):
    __tablename__ = "user_rewards"

    user_id   = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True, nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey("rewards.reward_id"), primary_key=True, nullable=False)
    earned_at = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    user   = db.relationship("User", back_populates="user_rewards")
    reward = db.relationship("Reward", back_populates="user_rewards")

    def __repr__(self):
        return f"<UserReward u={self.user_id} r={self.reward_id}>"

# ----- Activity Log -----
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    activity_id = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    action      = db.Column(db.String(255), nullable=False)
    timestamp   = db.Column(db.DateTime, nullable=False, default=UTC_NOW)

    user = db.relationship("User", back_populates="activity")

    def __repr__(self):
        return f"<Activity {self.activity_id} u={self.user_id} {self.action[:24]}>"


