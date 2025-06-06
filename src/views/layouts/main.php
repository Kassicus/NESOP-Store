<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= APP_NAME ?></title>
    <link rel="stylesheet" href="<?= APP_URL ?>/assets/css/style.css">
</head>
<body>
    <header>
        <nav>
            <div class="nav-brand">
                <a href="<?= APP_URL ?>"><?= APP_NAME ?></a>
            </div>
            <div class="nav-links">
                <?php if (isset($_SESSION['user_id'])): ?>
                    <a href="<?= APP_URL ?>/dashboard.php">Dashboard</a>
                    <a href="<?= APP_URL ?>/cart.php">Cart</a>
                    <a href="<?= APP_URL ?>/logout.php">Logout</a>
                <?php else: ?>
                    <a href="<?= APP_URL ?>/login.php">Login</a>
                <?php endif; ?>
            </div>
        </nav>
    </header>

    <main>
        <?php if (isset($_SESSION['flash_message'])): ?>
            <div class="flash-message <?= $_SESSION['flash_type'] ?? 'info' ?>">
                <?= $_SESSION['flash_message'] ?>
            </div>
            <?php unset($_SESSION['flash_message'], $_SESSION['flash_type']); ?>
        <?php endif; ?>

        <?= $content ?? '' ?>
    </main>

    <footer>
        <p>&copy; <?= date('Y') ?> <?= APP_NAME ?>. All rights reserved.</p>
    </footer>

    <script src="<?= APP_URL ?>/assets/js/main.js"></script>
</body>
</html> 