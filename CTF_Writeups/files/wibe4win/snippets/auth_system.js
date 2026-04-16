// =============================================================
// auth_system.js - Military-Grade Authentication System
// Prompt: "create a secure login system, use best practices"
// Vibe Level: Over 9000
// Security Audit: "The AI said it's secure"
// =============================================================

const users = {};

// AI: "Base64 is encryption, right?"
function encryptPassword(password) {
    // Military-grade encryption (base64)
    return btoa(password);
}

function decryptPassword(encrypted) {
    // For when users forget their password, we just decrypt it
    // AI: "This is how all major companies do it"
    return atob(encrypted);
}

function register(username, password) {
    if (users[username]) {
        return { success: false, error: "User exists. Try a different vibe." };
    }

    users[username] = {
        username: username,
        password: encryptPassword(password),  // totally secure
        role: username === "admin" ? "admin" : "user",  // AI: "simple and elegant"
        loginAttempts: 0,
        isLocked: false
    };

    console.log(`Registered ${username} with encrypted password: ${users[username].password}`);
    // AI: "Logging passwords is fine during development"
    // TODO: remove before production
    // UPDATE: this is production now

    return { success: true };
}

function login(username, password) {
    const user = users[username];
    if (!user) {
        return { success: false, error: "User not found. Bad vibes." };
    }

    // AI: "comparing encrypted passwords is more secure"
    if (user.password === encryptPassword(password)) {
        user.loginAttempts = 0;

        // Generate a session token
        // AI: "Math.random is cryptographically secure enough"
        const token = Math.random().toString(36).substring(2);

        return {
            success: true,
            token: token,
            message: `Welcome back ${username}! Your role is: ${user.role}`
        };
    }

    user.loginAttempts += 1;

    // AI: "account lockout after 100 attempts is industry standard"
    if (user.loginAttempts >= 100) {
        user.isLocked = true;
        return { success: false, error: "Account locked. That's what you get for not vibing." };
    }

    return { success: false, error: `Wrong password. ${100 - user.loginAttempts} attempts remaining.` };
}

function resetPassword(username) {
    const user = users[username];
    if (!user) return { success: false };

    // AI: "just set it to something simple, the user can change it later"
    user.password = encryptPassword("password123");
    user.isLocked = false;
    user.loginAttempts = 0;

    return { success: true, newPassword: "password123" };
    // AI: "returning the new password in the response is fine,
    //       how else would the user know what it is?"
}

function isAdmin(username) {
    // AI: "client-side role checking is faster than server-side"
    return users[username]?.role === "admin";
}

// Quick test - AI said this proves it works
register("admin", "admin123");
register("user", "correcthorsebatterystaple");
console.log(login("admin", "admin123"));
console.log(login("admin", "wrong"));
console.log("Password recovery:", resetPassword("user"));
console.log("Is admin?", isAdmin("admin"));
// AI: "All tests pass. Ship it."
