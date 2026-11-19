"""Streamlit helpers for cached engines and fresh database sessions."""

import streamlit as st
from sqlalchemy.orm import Session

from database.connection import engine


@st.cache_resource
def get_engine():
    """Cache the SQLAlchemy engine for the Streamlit process."""
    return engine


def get_session() -> Session:
    """Return a new SQLAlchemy session for the current page run."""
    return Session(bind=get_engine(), expire_on_commit=False)
