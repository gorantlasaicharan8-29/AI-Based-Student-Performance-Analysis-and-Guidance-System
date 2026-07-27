-- MySQL Database Dump
-- AI-Based Student Performance Analysis and Guidance System
-- Database: student_performance_db
-- ------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `role`, `department`, `created_at`, `is_active`) VALUES
(1, 'Dr. Rajesh Kumar', 'hod@college.edu', '$2b$12$UyoVE2x5KXgSwTOOzkje9uqE1TrlOIGWmDkbws1yI.QkOv086Y2W6', 'hod', 'Computer Science', '2026-07-27 17:45:10', 1),
(2, 'Prof. Anita Sharma', 'teacher@college.edu', '$2b$12$S.B6P4wqsQa12fMLybY7qu2sq0KsXDYkpzjtYz.KUXsc06H/809sK', 'teacher', 'Computer Science', '2026-07-27 17:45:10', 1),
(3, 'Prof. Vijay Patel', 'teacher2@college.edu', '$2b$12$G4piiroMVhvlRgjm6htayuFUzFOUboDRVMMoNn8.9VQzSU75FT.q2', 'teacher', 'Information Technology', '2026-07-27 17:45:10', 1),
(4, 'Gorantla Sai Charan', 'gorantlasaicharan@gmail.com', '$2b$12$91jUVD9gRvIOmvBW6AZycuFh/DWjcf4FcGEm3DF7RBlqe66SBh4Aq', 'student', 'Computer Science', '2026-07-24 09:38:04', 1),
(5, 'Charan Kumar', 'charankumar@gmail.com', '$2b$12$1W3ZtpbBG1KdYK3lX8DDTOyZHxPxe7xyNil8kdBDU53/4IXcgohSO', 'student', 'Computer Science', '2026-07-24 09:38:04', 1),
(6, 'Ganesh', 'ganesh@gmail.com', '$2b$12$dtov6vyyWa6ojs5H/QYm5OsIUkj15CsVMPnlPrnvTQ/CzgYDuGclS', 'student', 'Computer Science', '2026-07-24 09:38:04', 1),
(7, 'Chitra', 'chitramec@gmail.com', '$2b$12$0KBp4BnkGpo2LnNtpw3/ReUK3ncD4fxJHSF2XdwdkK5ebziWuKwcq', 'teacher', 'Computer Science', '2026-07-25 14:54:00', 1),
(8, 'Ananth', 'mecananths@gmail.com', '$2b$12$D/8z4Py6eozuU44WH8.6quaHvk5gCA.SQCdxEUCca9C1CQeB/vcYy', 'hod', 'Computer Science', '2026-07-27 13:42:53', 1),
(9, 'Sowmith', 'sowmith@gmail.com', '$2b$12$yb6UjvqlTJVnDRxtX.VpP.sY3pSCCGWf2k8/QsV5shZ5VD6Bq/10G', 'student', 'Computer Science', '2026-07-27 13:55:55', 1),
(10, 'Shaik Ashik', 'shaikashik@gmail.com', '$2b$12$LrUocaFvjbZhHDPdZ9D5ReVnxikgDy04hEBYMM4dQI1vCs/SRvePW', 'student', 'Computer Science', '2026-07-27 13:55:55', 1);

DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `roll_number` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `semester` int DEFAULT NULL,
  `batch` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `roll_number` (`roll_number`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `students` (`id`, `user_id`, `roll_number`, `department`, `semester`, `batch`) VALUES
(1, 4, 'CS2024001', 'Computer Science', 4, '2024'),
(2, 5, 'CS2024002', 'Computer Science', 4, '2024'),
(3, 6, 'CS2024003', 'Computer Science', 4, '2024'),
(4, 9, 'CS2024004', 'Computer Science', 4, '2024'),
(5, 10, 'CS2024005', 'Computer Science', 4, '2024');

DROP TABLE IF EXISTS `subjects`;
CREATE TABLE `subjects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `semester` int DEFAULT NULL,
  `max_marks` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `subjects` (`id`, `name`, `department`, `semester`, `max_marks`) VALUES
(1, 'Data Structures', 'Computer Science', 4, 100.0),
(2, 'Operating Systems', 'Computer Science', 4, 100.0),
(3, 'Database Management', 'Computer Science', 4, 100.0),
(4, 'Computer Networks', 'Computer Science', 4, 100.0),
(5, 'Algorithms', 'Computer Science', 4, 100.0),
(6, 'Web Technologies', 'Information Technology', 3, 100.0),
(7, 'Software Engineering', 'Information Technology', 3, 100.0),
(8, 'Python Programming', 'Information Technology', 3, 100.0);

DROP TABLE IF EXISTS `marks`;
CREATE TABLE `marks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `subject_id` int NOT NULL,
  `marks` float NOT NULL,
  `attendance` float DEFAULT NULL,
  `assignment_score` float DEFAULT NULL,
  `recorded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `subject_id` (`subject_id`),
  CONSTRAINT `marks_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`),
  CONSTRAINT `marks_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `marks` (`id`, `student_id`, `subject_id`, `marks`, `attendance`, `assignment_score`, `recorded_at`) VALUES
(1, 1, 1, 78.0, 89.0, 85.0, '2026-07-27 13:47:22'),
(2, 1, 2, 80.0, 95.0, 88.0, '2026-07-27 13:47:22'),
(3, 1, 3, 85.0, 80.0, 82.0, '2026-07-27 13:47:22'),
(4, 1, 4, 75.0, 78.0, 80.0, '2026-07-27 13:47:22'),
(5, 1, 5, 80.0, 77.0, 88.0, '2026-07-27 13:47:22'),
(6, 2, 1, 95.0, 92.0, 90.0, '2026-07-27 13:50:57'),
(7, 2, 2, 88.0, 90.0, 82.0, '2026-07-27 13:50:57'),
(8, 2, 3, 89.0, 97.0, 96.0, '2026-07-27 13:50:57'),
(9, 2, 4, 88.0, 79.0, 87.0, '2026-07-27 13:50:57'),
(10, 2, 5, 90.0, 80.0, 90.0, '2026-07-27 13:50:57'),
(11, 3, 1, 85.0, 90.0, 90.0, '2026-07-27 13:52:39'),
(12, 3, 2, 79.0, 90.0, 90.0, '2026-07-27 13:52:39'),
(13, 3, 3, 88.0, 87.0, 88.0, '2026-07-27 13:52:39'),
(14, 3, 4, 79.0, 80.0, 90.0, '2026-07-27 13:52:39'),
(15, 3, 5, 90.0, 88.0, 95.0, '2026-07-27 13:52:39'),
(16, 4, 1, 77.0, 85.0, 88.0, '2026-07-27 13:58:21'),
(17, 4, 2, 85.0, 85.0, 90.0, '2026-07-27 13:58:21'),
(18, 4, 3, 90.0, 85.0, 85.0, '2026-07-27 13:58:21'),
(19, 4, 4, 70.0, 75.0, 80.0, '2026-07-27 13:58:21'),
(20, 4, 5, 71.0, 75.0, 90.0, '2026-07-27 13:58:21'),
(21, 5, 1, 85.0, 88.0, 95.0, '2026-07-27 13:59:07'),
(22, 5, 2, 75.0, 95.0, 85.0, '2026-07-27 13:59:07'),
(23, 5, 3, 79.0, 88.0, 95.0, '2026-07-27 13:59:07'),
(24, 5, 4, 69.0, 85.0, 79.0, '2026-07-27 13:59:07'),
(25, 5, 5, 69.0, 75.0, 75.0, '2026-07-27 13:59:07');

DROP TABLE IF EXISTS `units`;
CREATE TABLE `units` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subject_id` int NOT NULL,
  `unit_number` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_subject_unit` (`subject_id`,`unit_number`),
  CONSTRAINT `units_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`),
  CONSTRAINT `ck_unit_number_range` CHECK ((`unit_number` between 1 and 6))
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `units` (`id`, `subject_id`, `unit_number`, `title`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'Introduction to Data Structures', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(2, 1, 2, 'Trees and Binary Trees', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(3, 1, 3, 'Graphs', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(4, 1, 4, 'Hashing', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(5, 1, 5, 'Heaps and Priority Queues', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(6, 1, 6, 'Advanced Topics', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(7, 2, 1, 'OS Fundamentals', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(8, 2, 2, 'Process Management', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(9, 2, 3, 'Memory Management', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(10, 2, 4, 'File Systems', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(11, 2, 5, 'Deadlocks', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(12, 2, 6, 'I/O and Security', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(13, 3, 1, 'Introduction to DBMS', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(14, 3, 2, 'SQL Fundamentals', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(15, 3, 3, 'Normalization', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(16, 3, 4, 'Transactions & Concurrency', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(17, 3, 5, 'Indexing & Query Optimization', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(18, 3, 6, 'Advanced Database Topics', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(19, 4, 1, 'Network Fundamentals', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(20, 4, 2, 'Data Link Layer', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(21, 4, 3, 'Network Layer', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(22, 4, 4, 'Transport Layer', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(23, 4, 5, 'Application Layer', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(24, 4, 6, 'Network Security', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(25, 5, 1, 'Algorithm Analysis', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(26, 5, 2, 'Sorting & Searching', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(27, 5, 3, 'Divide and Conquer', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(28, 5, 4, 'Dynamic Programming', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(29, 5, 5, 'Greedy Algorithms', '2026-07-27 17:45:10', '2026-07-27 17:45:10'),
(30, 5, 6, 'NP-Completeness', '2026-07-27 17:45:10', '2026-07-27 17:45:10');

DROP TABLE IF EXISTS `topics`;
CREATE TABLE `topics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `unit_id` int NOT NULL,
  `name` varchar(300) COLLATE utf8mb4_unicode_ci NOT NULL,
  `order` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `unit_id` (`unit_id`),
  CONSTRAINT `topics_ibfk_1` FOREIGN KEY (`unit_id`) REFERENCES `units` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `topics` (`id`, `unit_id`, `name`, `order`) VALUES
(1, 1, 'Arrays', 0),
(2, 1, 'Linked Lists', 1),
(3, 1, 'Stacks', 2),
(4, 1, 'Queues', 3),
(5, 2, 'Binary Tree', 0),
(6, 2, 'BST', 1),
(7, 2, 'Tree Traversals', 2),
(8, 2, 'AVL Trees', 3),
(9, 3, 'Graph Representation', 0),
(10, 3, 'BFS', 1),
(11, 3, 'DFS', 2),
(12, 3, 'Shortest Path', 3),
(13, 4, 'Hash Functions', 0),
(14, 4, 'Collision Resolution', 1),
(15, 4, 'Hash Tables', 2),
(16, 5, 'Min-Heap', 0),
(17, 5, 'Max-Heap', 1),
(18, 5, 'Heap Sort', 2),
(19, 5, 'Priority Queue', 3),
(20, 6, 'Tries', 0),
(21, 6, 'Segment Trees', 1),
(22, 6, 'Disjoint Sets', 2),
(23, 6, 'Complexity Analysis', 3),
(24, 7, 'OS Structure', 0),
(25, 7, 'System Calls', 1),
(26, 7, 'OS Types', 2),
(27, 8, 'Process States', 0),
(28, 8, 'PCB', 1),
(29, 8, 'Scheduling Algorithms', 2),
(30, 9, 'Paging', 0),
(31, 9, 'Segmentation', 1),
(32, 9, 'Virtual Memory', 2),
(33, 10, 'File Concepts', 0),
(34, 10, 'Directory Structure', 1),
(35, 10, 'Allocation Methods', 2),
(36, 11, 'Deadlock Conditions', 0),
(37, 11, 'Prevention', 1),
(38, 11, 'Banker\'s Algorithm', 2),
(39, 12, 'I/O Hardware', 0),
(40, 12, 'Disk Scheduling', 1),
(41, 12, 'Protection & Security', 2),
(42, 13, 'DBMS Concepts', 0),
(43, 13, 'ER Model', 1),
(44, 13, 'Relational Model', 2),
(45, 14, 'DDL', 0),
(46, 14, 'DML', 1),
(47, 14, 'SELECT Queries', 2),
(48, 14, 'Joins', 3),
(49, 15, '1NF', 0),
(50, 15, '2NF', 1),
(51, 15, '3NF', 2),
(52, 15, 'BCNF', 3),
(53, 16, 'ACID Properties', 0),
(54, 16, 'Serializability', 1),
(55, 16, 'Locks', 2),
(56, 17, 'B-Tree Index', 0),
(57, 17, 'Query Plans', 1),
(58, 17, 'Optimization Techniques', 2),
(59, 18, 'NoSQL', 0),
(60, 18, 'Distributed DB', 1),
(61, 18, 'Data Warehousing', 2),
(62, 19, 'OSI Model', 0),
(63, 19, 'TCP/IP Model', 1),
(64, 19, 'Topologies', 2),
(65, 20, 'Framing', 0),
(66, 20, 'Error Detection', 1),
(67, 20, 'MAC Protocols', 2),
(68, 21, 'IP Addressing', 0),
(69, 21, 'Subnetting', 1),
(70, 21, 'Routing Protocols', 2),
(71, 22, 'TCP', 0),
(72, 22, 'UDP', 1),
(73, 22, 'Flow Control', 2),
(74, 22, 'Congestion Control', 3),
(75, 23, 'HTTP', 0),
(76, 23, 'DNS', 1),
(77, 23, 'FTP', 2),
(78, 23, 'SMTP', 3),
(79, 23, 'DHCP', 4),
(80, 24, 'Cryptography', 0),
(81, 24, 'Firewalls', 1),
(82, 24, 'VPN', 2),
(83, 24, 'SSL/TLS', 3),
(84, 25, 'Time Complexity', 0),
(85, 25, 'Space Complexity', 1),
(86, 25, 'Big-O Notation', 2),
(87, 26, 'Merge Sort', 0),
(88, 26, 'Quick Sort', 1),
(89, 26, 'Binary Search', 2),
(90, 27, 'Strassen\'s Algorithm', 0),
(91, 27, 'Closest Pair', 1),
(92, 27, 'FFT', 2),
(93, 28, 'Memoization', 0),
(94, 28, 'LCS', 1),
(95, 28, 'Knapsack', 2),
(96, 28, 'Matrix Chain', 3),
(97, 29, 'Huffman Coding', 0),
(98, 29, 'Kruskal', 1),
(99, 29, 'Prim\'s Algorithm', 2),
(100, 30, 'P vs NP', 0),
(101, 30, 'NP-Hard Problems', 1),
(102, 30, 'Approximation Algorithms', 2);

DROP TABLE IF EXISTS `assignments`;
CREATE TABLE `assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `teacher_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `deadline` datetime DEFAULT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `original_filename` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `target_department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `target_student_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `teacher_id` (`teacher_id`),
  KEY `target_student_id` (`target_student_id`),
  CONSTRAINT `assignments_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`),
  CONSTRAINT `assignments_ibfk_2` FOREIGN KEY (`target_student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `assignments` (`id`, `teacher_id`, `title`, `description`, `deadline`, `file_path`, `original_filename`, `target_department`, `target_student_id`, `created_at`, `updated_at`, `is_active`) VALUES
(1, 7, 'Data Structures Assignment – Fundamentals of Linear Data Structures', 'This assignment is designed to strengthen students\' understanding of the fundamental concepts of Data Structures, focusing on arrays, linked lists, stacks, queues, recursion, and time complexity. Students will compare different data structures, analyze their real-world applications, and solve both theoretical and practical problems to improve problem-solving and programming skills.', '2026-07-31 11:59:00', 'assignments\\5c01cb7f06754d92ae186abcb170bd75.docx', 'Data_Structures_Assignment.docx', NULL, NULL, '2026-07-27 14:09:19', '2026-07-27 14:09:19', 1),
(2, 7, 'Operating Systems Assignment – Process Management and Memory Management', 'This assignment helps students understand the core concepts of Operating Systems, including process management, CPU scheduling, memory management, deadlocks, file systems, and synchronization. It develops analytical thinking through theoretical questions and real-world operating system scenarios.', '2026-08-04 11:59:00', 'assignments\\47af9ad5841345f2babdb3b266190d01.xlsx', 'Operating_System_Assignment.xlsx', 'Computer Science', NULL, '2026-07-27 14:17:14', '2026-07-27 14:17:14', 1);

DROP TABLE IF EXISTS `submissions`;
CREATE TABLE `submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assignment_id` int NOT NULL,
  `student_id` int NOT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `original_filename` varchar(300) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grade` float DEFAULT NULL,
  `feedback` text COLLATE utf8mb4_unicode_ci,
  `submitted_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `assignment_id` (`assignment_id`),
  KEY `student_id` (`student_id`),
  CONSTRAINT `submissions_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),
  CONSTRAINT `submissions_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `predictions`;
CREATE TABLE `predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `grade` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `risk_level` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `confidence` float DEFAULT NULL,
  `factors` text COLLATE utf8mb4_unicode_ci,
  `recommendations` text COLLATE utf8mb4_unicode_ci,
  `average_marks` float DEFAULT NULL,
  `average_attendance` float DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  CONSTRAINT `predictions_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `predictions` (`id`, `student_id`, `grade`, `risk_level`, `confidence`, `factors`, `recommendations`, `average_marks`, `average_attendance`, `created_at`) VALUES
(1, 1, 'B', 'Low', 85.1, '[{"factor": "Good academic marks", "impact": "positive", "value": "79.6%"}, {"factor": "Good attendance record", "impact": "positive", "value": "83.8%"}, {"factor": "4 subject(s) above distinction threshold", "impact": "positive", "value": "4 subjects"}, {"factor": "Excellent assignment completion", "impact": "positive", "value": "100%"}]', '["Great job maintaining low academic risk!", "Stay consistent with your study schedule", "Challenge yourself with extra-curricular academic activities", "Identify the 2\\u20133 topics where you lose most marks and focus there", "Practice time management during exams"]', 79.6, 83.8, '2026-07-27 13:47:53'),
(2, 2, 'A', 'Low', 86.8, '[{"factor": "Excellent academic marks", "impact": "positive", "value": "90.0%"}, {"factor": "Good attendance record", "impact": "positive", "value": "87.6%"}, {"factor": "5 subject(s) above distinction threshold", "impact": "positive", "value": "5 subjects"}, {"factor": "Excellent assignment completion", "impact": "positive", "value": "100%"}]', '["Great job maintaining low academic risk!", "Stay consistent with your study schedule", "Challenge yourself with extra-curricular academic activities", "Maintain your excellent performance \\u2014 consistency is key", "Consider mentoring struggling peers to reinforce your knowledge"]', 90.0, 87.6, '2026-07-27 13:53:00'),
(3, 3, 'B', 'Low', 77.6, '[{"factor": "Good academic marks", "impact": "positive", "value": "84.2%"}, {"factor": "Good attendance record", "impact": "positive", "value": "87.0%"}, {"factor": "5 subject(s) above distinction threshold", "impact": "positive", "value": "5 subjects"}, {"factor": "Excellent assignment completion", "impact": "positive", "value": "100%"}]', '["Great job maintaining low academic risk!", "Stay consistent with your study schedule", "Challenge yourself with extra-curricular academic activities", "Identify the 2\\u20133 topics where you lose most marks and focus there", "Practice time management during exams"]', 84.2, 87.0, '2026-07-27 13:53:46'),
(4, 5, 'B', 'Low', 89.1, '[{"factor": "Good academic marks", "impact": "positive", "value": "75.4%"}, {"factor": "Good attendance record", "impact": "positive", "value": "86.2%"}, {"factor": "2 subject(s) above distinction threshold", "impact": "positive", "value": "2 subjects"}, {"factor": "Excellent assignment completion", "impact": "positive", "value": "100%"}]', '["Great job maintaining low academic risk!", "Stay consistent with your study schedule", "Challenge yourself with extra-curricular academic activities", "Identify the 2\\u20133 topics where you lose most marks and focus there", "Practice time management during exams"]', 75.4, 86.2, '2026-07-27 14:10:43'),
(5, 5, 'B', 'Low', 89.1, '[{"factor": "Good academic marks", "impact": "positive", "value": "75.4%"}, {"factor": "Good attendance record", "impact": "positive", "value": "86.2%"}, {"factor": "2 subject(s) above distinction threshold", "impact": "positive", "value": "2 subjects"}, {"factor": "Excellent assignment completion", "impact": "positive", "value": "100%"}]', '["Great job maintaining low academic risk!", "Stay consistent with your study schedule", "Challenge yourself with extra-curricular academic activities", "Identify the 2\\u20133 topics where you lose most marks and focus there", "Practice time management during exams"]', 75.4, 86.2, '2026-07-27 14:53:34');

DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `notification_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `notifications` (`id`, `user_id`, `title`, `message`, `is_read`, `created_at`, `notification_type`) VALUES
(1, 2, 'Welcome to AI Student Performance System!', 'Hello Prof. Anita Sharma! Your teacher account is ready. Explore your dashboard.', 0, '2026-07-27 17:45:10', 'success'),
(2, 1, 'Welcome to AI Student Performance System!', 'Hello Dr. Rajesh Kumar! Your hod account is ready. Explore your dashboard.', 0, '2026-07-27 17:45:10', 'success'),
(3, 4, 'Welcome to AI Student Performance System!', 'Hello Gorantla Sai Charan! Your student account is ready. Login to explore your dashboard.', 0, '2026-07-24 09:38:04', 'success'),
(4, 5, 'Welcome to AI Student Performance System!', 'Hello Charan Kumar! Your student account is ready. Login to explore your dashboard.', 0, '2026-07-24 09:38:04', 'success'),
(5, 6, 'Welcome to AI Student Performance System!', 'Hello Ganesh! Your student account is ready. Login to explore your dashboard.', 0, '2026-07-24 09:38:04', 'success'),
(6, 7, 'Welcome to AI Student Performance System!', 'Hello Chitra! Your teacher account is ready. Login to explore your dashboard.', 0, '2026-07-25 14:54:00', 'success'),
(7, 8, 'Welcome to AI Student Performance System!', 'Hello Ananth! Your HOD account is ready. Login to explore your dashboard.', 0, '2026-07-27 13:42:53', 'success'),
(8, 4, '📊 Marks Updated', 'Your marks have been updated by Chitra.', 0, '2026-07-27 13:47:22', 'info'),
(9, 5, '📊 Marks Updated', 'Your marks have been updated by Chitra.', 0, '2026-07-27 13:50:57', 'info'),
(10, 6, '📊 Marks Updated', 'Your marks have been updated by Chitra.', 0, '2026-07-27 13:52:39', 'info'),
(11, 9, 'Welcome to AI Student Performance System!', 'Hello Sowmith! Your student account is ready. Login to explore your dashboard.', 0, '2026-07-27 13:55:55', 'success'),
(12, 10, 'Welcome to AI Student Performance System!', 'Hello Shaik Ashik! Your student account is ready. Login to explore your dashboard.', 0, '2026-07-27 13:55:55', 'success'),
(13, 9, '📊 Marks Updated', 'Your marks have been updated by Chitra.', 0, '2026-07-27 13:58:21', 'info'),
(14, 10, '📊 Marks Updated', 'Your marks have been updated by Chitra.', 0, '2026-07-27 13:59:07', 'info'),
(15, 4, '📋 New Assignment', '\'Data Structures Assignment – Fundamentals of Linear Data Structures\' assigned by Chitra. Deadline: 2026-07-31 11:59:00', 0, '2026-07-27 14:09:19', 'info'),
(16, 5, '📋 New Assignment', '\'Data Structures Assignment – Fundamentals of Linear Data Structures\' assigned by Chitra. Deadline: 2026-07-31 11:59:00', 0, '2026-07-27 14:09:19', 'info'),
(17, 6, '📋 New Assignment', '\'Data Structures Assignment – Fundamentals of Linear Data Structures\' assigned by Chitra. Deadline: 2026-07-31 11:59:00', 0, '2026-07-27 14:09:19', 'info'),
(18, 9, '📋 New Assignment', '\'Data Structures Assignment – Fundamentals of Linear Data Structures\' assigned by Chitra. Deadline: 2026-07-31 11:59:00', 0, '2026-07-27 14:09:19', 'info'),
(19, 10, '📋 New Assignment', '\'Data Structures Assignment – Fundamentals of Linear Data Structures\' assigned by Chitra. Deadline: 2026-07-31 11:59:00', 0, '2026-07-27 14:09:19', 'info'),
(20, 4, '📋 New Assignment', '\'Operating Systems Assignment – Process Management and Memory Management\' assigned by Chitra. Deadline: 2026-08-04 11:59:00', 0, '2026-07-27 14:17:14', 'info'),
(21, 5, '📋 New Assignment', '\'Operating Systems Assignment – Process Management and Memory Management\' assigned by Chitra. Deadline: 2026-08-04 11:59:00', 0, '2026-07-27 14:17:14', 'info'),
(22, 6, '📋 New Assignment', '\'Operating Systems Assignment – Process Management and Memory Management\' assigned by Chitra. Deadline: 2026-08-04 11:59:00', 0, '2026-07-27 14:17:14', 'info'),
(23, 9, '📋 New Assignment', '\'Operating Systems Assignment – Process Management and Memory Management\' assigned by Chitra. Deadline: 2026-08-04 11:59:00', 0, '2026-07-27 14:17:14', 'info'),
(24, 10, '📋 New Assignment', '\'Operating Systems Assignment – Process Management and Memory Management\' assigned by Chitra. Deadline: 2026-08-04 11:59:00', 0, '2026-07-27 14:17:14', 'info');

SET FOREIGN_KEY_CHECKS = 1;
