# Use Ubuntu 18.04 as the base image
FROM ubuntu:18.04

# Set the maintainer label
LABEL maintainer="your_email@example.com"

# Update the package list and install Python and Pip
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies from requirements.txt
RUN pip3 install -r requirements.txt

# Copy the entire application to the container
COPY . /app

# Set the entry point and default command to run the specified app.py
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
