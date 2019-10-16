#!/bin/bash
sudo a2enmod cgid
sudo apt-get install python3-lxml
sudo systemctl restart apache2
