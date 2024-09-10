CREATE USER 'uaas'@'localhost' IDENTIFIED BY 'uaas-password';

CREATE USER 'uaas'@'%' IDENTIFIED BY 'uaas-password';


create database uaas_db;

GRANT ALL PRIVILEGES on uaas_db.* to 'uaas'@'localhost';

GRANT ALL PRIVILEGES on uaas_db.* to 'uaas'@'%';