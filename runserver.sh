#!/bin/bash

flask initdb
flask create_providers
flask create_participant

flask run --host 0.0.0.0
