# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

# Install production dependencies.
RUN pip install git+https://github.com/sambarnes/alchemy.git
RUN pip install click

# Default config
ENV NODE_TYPE cloud

# Run it
CMD python app.py --node-type=$NODE_TYPE
