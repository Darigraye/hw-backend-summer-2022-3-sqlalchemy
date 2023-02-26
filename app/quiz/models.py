from dataclasses import dataclass

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Boolean,
    NUMERIC,
    PrimaryKeyConstraint,
    TIMESTAMP,
    Text,
    VARCHAR,
    String,
)

from sqlalchemy.orm import relationship
from app.store.database.sqlalchemy_base import db


@dataclass
class Theme:
    id: int
    title: str


@dataclass
class Question:
    id: int
    title: str
    theme_id: int
    answers: list["Answer"]


@dataclass
class Answer:
    title: str
    is_correct: bool


class ThemeModel(db):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)


class QuestionModel(db):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    theme_id = Column(Integer, ForeignKey('themes.id', ondelete='CASCADE'), nullable=False)
    answers = relationship('AnswerModel', backref='question_model')


class AnswerModel(db):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
