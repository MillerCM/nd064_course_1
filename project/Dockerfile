FROM python:2.7
LABEL maintainer="Christina Miller"

COPY ./techtrends /techtrends
WORKDIR /techtrends
# open port 3111
EXPOSE 3111
# install package requirements
RUN pip install -r requirements.txt
# initialize database
RUN python init_db.py

# run app on container start
CMD [ "python", "app.py" ]
