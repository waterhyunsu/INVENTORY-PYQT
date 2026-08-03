CREATE TABLE `item` (
  `nsn` varchar(30) NOT NULL,
  `name` varchar(50) NOT NULL COMMENT '품명',
  `price` int NOT NULL COMMENT '조달단가',
  `stock` int NOT NULL COMMENT '보유수량',
  PRIMARY KEY (`nsn`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



CREATE TABLE `history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `user_id` varchar(50) DEFAULT NULL,
  `nsn` varchar(50) DEFAULT NULL,
  `item_name` varchar(100) DEFAULT NULL,
  `action_type` varchar(20) DEFAULT NULL,
  `qty_change` int DEFAULT NULL,
  `current_stock` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=563 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;




CREATE TABLE `users` (
  `user_id` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
