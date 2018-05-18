import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Genre(Base):
    __tablename__ = "genre"

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def list(self):
        return {
            'name': self.name,
            'id': self.id,
        }

class Books(Base):
    __tablename__ = "books"

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    author = Column(String(80), nullable = False)
    description = Column(String(500))
    price = Column(String(8))
    rating = Column(Integer)
    genre_id = Column(Integer, ForeignKey("genre.id"))
    genre = relationship(Genre)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'id': self.id,
            'price': self.price,
            'rating': self.rating,
        }



engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.create_all(engine)
