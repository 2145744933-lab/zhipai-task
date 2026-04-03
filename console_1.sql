CREATE DATABASE zhipai_task_system CHARACTER SET utf8mb4;
USE zhipai_task_system;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL,
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    publisher_id INT,
    status VARCHAR(20) DEFAULT '未完成',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_receives (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT,
    user_id INT,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (task_id,user_id)
);

CREATE TABLE comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT,
    user_id INT,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);