FROM ubuntu
LABEL maintainer="kagdakj kagdakj@kagdakj.us.to"
LABEL description="kagdakj's gbs_timetable flask application"

# Create app directory
WORKDIR /app

RUN apt autoremove
RUN apt clean
RUN apt update
RUN apt install python3 python3-pip python3-flask -y
RUN pip install pycomcigan --break-system-packages
RUN pip install cachetools --break-system-packages
# If you are building your code for production
# RUN npm ci --only=production

# Bundle app source
COPY . .

EXPOSE 80
CMD [ "python3", "server.py" ]