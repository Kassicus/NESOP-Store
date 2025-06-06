<?php
/**
 * Database Connection Class
 * 
 * Handles database connections and provides basic query functionality
 */
class Database {
    private static $instance = null;
    private $connection;
    private $statement;

    /**
     * Private constructor to prevent direct instantiation
     */
    private function __construct() {
        try {
            $this->connection = new PDO(
                "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
                DB_USER,
                DB_PASS,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false
                ]
            );
        } catch (PDOException $e) {
            // Log the error
            error_log("Database Connection Error: " . $e->getMessage());
            throw new Exception("Database connection failed. Please try again later.");
        }
    }

    /**
     * Get database instance (Singleton pattern)
     */
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Prepare and execute a query
     */
    public function query($sql, $params = []) {
        try {
            $this->statement = $this->connection->prepare($sql);
            $this->statement->execute($params);
            return $this;
        } catch (PDOException $e) {
            error_log("Query Error: " . $e->getMessage());
            throw new Exception("Database query failed. Please try again later.");
        }
    }

    /**
     * Fetch all results
     */
    public function fetchAll() {
        return $this->statement->fetchAll();
    }

    /**
     * Fetch single result
     */
    public function fetch() {
        return $this->statement->fetch();
    }

    /**
     * Get row count
     */
    public function rowCount() {
        return $this->statement->rowCount();
    }

    /**
     * Get last inserted ID
     */
    public function lastInsertId() {
        return $this->connection->lastInsertId();
    }

    /**
     * Begin transaction
     */
    public function beginTransaction() {
        return $this->connection->beginTransaction();
    }

    /**
     * Commit transaction
     */
    public function commit() {
        return $this->connection->commit();
    }

    /**
     * Rollback transaction
     */
    public function rollBack() {
        return $this->connection->rollBack();
    }
} 