#!/bin/bash
gunicorn -w 1 app:app
