# API安全最佳实践指南

## 概述

本文档详细阐述API设计、实现和部署中的安全最佳实践，涵盖认证、授权、输入验证、限流、数据保护等关键领域。

---

## 1. API认证与授权

### 1.1 认证方案对比

| 方案           | 适用场景             | 优点                   | 缺点                     | 安全等级   |
| -------------- | -------------------- | ---------------------- | ------------------------ | ---------- |
| **API Key**    | 服务间通信、简单场景 | 实现简单、易于管理     | 无法撤销单个密钥、易泄露 | ⭐⭐       |
| **Basic Auth** | 内部系统、开发环境   | 实现简单               | 凭证易泄露、需HTTPS      | ⭐⭐       |
| **JWT**        | 无状态认证、移动应用 | 可扩展、无状态、跨域   | 无法立即撤销、需安全存储 | ⭐⭐⭐     |
| **OAuth 2.0**  | 第三方授权、SSO      | 安全、灵活、权限细粒度 | 实现复杂、流程多         | ⭐⭐⭐⭐   |
| **mTLS**       | 服务网格、高安全     | 双向认证、无密码       | 证书管理复杂、性能开销   | ⭐⭐⭐⭐⭐ |

### 1.2 JWT实现最佳实践

**生成安全的JWT：**

```javascript
const jwt = require("jsonwebtoken");
const crypto = require("crypto");

// 1. 使用强密钥（至少256位）
const JWT_SECRET =
  process.env.JWT_SECRET || crypto.randomBytes(32).toString("hex");

// 2. 生成访问令牌（短期）
function generateAccessToken(user) {
  return jwt.sign(
    {
      userId: user.id,
      email: user.email,
      role: user.role,
      // 不要在JWT中存储敏感信息
    },
    JWT_SECRET,
    {
      expiresIn: "15m", // 15分钟过期
      issuer: "your-app", // 发行者
      audience: "your-app-users", // 受众
      algorithm: "HS256", // 算法
    },
  );
}

// 3. 生成刷新令牌（长期）
function generateRefreshToken(user) {
  return jwt.sign({ userId: user.id }, process.env.JWT_REFRESH_SECRET, {
    expiresIn: "7d",
    issuer: "your-app",
    algorithm: "HS256",
  });
}

// 4. 验证JWT
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, {
      issuer: "your-app",
      audience: "your-app-users",
      algorithms: ["HS256"],
    });
  } catch (err) {
    if (err.name === "TokenExpiredError") {
      throw new Error("Token expired");
    }
    if (err.name === "JsonWebTokenError") {
      throw new Error("Invalid token");
    }
    throw err;
  }
}

// 5. 刷新令牌流程
app.post("/api/auth/refresh", (req, res) => {
  const { refreshToken } = req.body;

  try {
    const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET);
    const user = getUserById(decoded.userId);

    // 检查刷新令牌是否在黑名单中
    if (isTokenBlacklisted(refreshToken)) {
      return res.status(401).json({ error: "Token revoked" });
    }

    const newAccessToken = generateAccessToken(user);
    res.json({ accessToken: newAccessToken });
  } catch (err) {
    res.status(401).json({ error: "Invalid refresh token" });
  }
});
```

**JWT令牌黑名单管理：**

```javascript
// 使用Redis存储黑名单
const redis = require("redis");
const client = redis.createClient();

// 登出时将令牌加入黑名单
app.post("/api/auth/logout", authenticateToken, (req, res) => {
  const token = req.headers.authorization.split(" ")[1];
  const decoded = jwt.decode(token);

  // 计算令牌剩余有效期
  const ttl = decoded.exp - Math.floor(Date.now() / 1000);

  if (ttl > 0) {
    // 将令牌加入黑名单，TTL为剩余有效期
    client.setex(`blacklist:${token}`, ttl, "true");
  }

  res.json({ message: "Logged out successfully" });
});

// 验证令牌时检查黑名单
function authenticateToken(req, res, next) {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({ error: "Access token required" });
  }

  // 检查黑名单
  client.get(`blacklist:${token}`, (err, result) => {
    if (result) {
      return res.status(401).json({ error: "Token revoked" });
    }

    try {
      const user = verifyToken(token);
      req.user = user;
      next();
    } catch (err) {
      res.status(403).json({ error: err.message });
    }
  });
}
```

### 1.3 OAuth 2.0授权码流程

```javascript
// 1. 用户点击"使用Google登录"
app.get("/api/auth/google", (req, res) => {
  const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  authUrl.searchParams.append("client_id", process.env.GOOGLE_CLIENT_ID);
  authUrl.searchParams.append(
    "redirect_uri",
    `${process.env.APP_URL}/api/auth/google/callback`,
  );
  authUrl.searchParams.append("response_type", "code");
  authUrl.searchParams.append("scope", "openid email profile");
  authUrl.searchParams.append("state", generateRandomState()); // CSRF防护

  res.redirect(authUrl.toString());
});

// 2. Google重定向回调
app.get("/api/auth/google/callback", async (req, res) => {
  const { code, state } = req.query;

  // 验证state防止CSRF
  if (!verifyState(state)) {
    return res.status(400).json({ error: "Invalid state" });
  }

  try {
    // 3. 使用授权码交换访问令牌
    const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        client_id: process.env.GOOGLE_CLIENT_ID,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        redirect_uri: `${process.env.APP_URL}/api/auth/google/callback`,
        grant_type: "authorization_code",
      }),
    });

    const { access_token, id_token } = await tokenResponse.json();

    // 4. 验证ID令牌
    const decoded = jwt.decode(id_token);
    const user = await findOrCreateUser(decoded);

    // 5. 生成应用的JWT
    const appToken = generateAccessToken(user);

    res.redirect(`${process.env.APP_URL}?token=${appToken}`);
  } catch (err) {
    res.status(500).json({ error: "Authentication failed" });
  }
});
```

### 1.4 基于角色的访问控制（RBAC）

```javascript
// 定义权限矩阵
const permissions = {
  admin: {
    users: ["create", "read", "update", "delete"],
    posts: ["create", "read", "update", "delete"],
    settings: ["read", "update"],
  },
  editor: {
    users: ["read"],
    posts: ["create", "read", "update"],
    settings: ["read"],
  },
  viewer: {
    users: ["read"],
    posts: ["read"],
    settings: [],
  },
};

// 权限检查中间件
function authorize(resource, action) {
  return (req, res, next) => {
    const userRole = req.user.role;
    const userPermissions = permissions[userRole] || {};
    const resourcePermissions = userPermissions[resource] || [];

    if (!resourcePermissions.includes(action)) {
      return res.status(403).json({
        error: "Forbidden",
        message: `User role '${userRole}' cannot ${action} ${resource}`,
      });
    }

    next();
  };
}

// 使用
app.post(
  "/api/posts",
  authenticateToken,
  authorize("posts", "create"),
  createPostHandler,
);

app.delete(
  "/api/users/:id",
  authenticateToken,
  authorize("users", "delete"),
  deleteUserHandler,
);
```

---

## 2. 输入验证与防注入

### 2.1 SQL注入防护

**❌ 易受攻击的代码：**

```javascript
// 字符串拼接 - SQL注入漏洞
app.get("/api/users/:id", (req, res) => {
  const userId = req.params.id;
  const query = `SELECT * FROM users WHERE id = ${userId}`;
  db.query(query, (err, results) => {
    res.json(results);
  });
});

// 攻击示例：GET /api/users/1 OR 1=1
// 执行的SQL：SELECT * FROM users WHERE id = 1 OR 1=1
// 结果：返回所有用户
```

**✅ 安全的代码：**

```javascript
// 方案1：参数化查询
app.get("/api/users/:id", (req, res) => {
  const userId = req.params.id;
  const query = "SELECT * FROM users WHERE id = ?";
  db.query(query, [userId], (err, results) => {
    res.json(results);
  });
});

// 方案2：使用ORM
app.get("/api/users/:id", async (req, res) => {
  const user = await User.findById(req.params.id);
  res.json(user);
});

// 方案3：使用查询构建器
app.get("/api/users/:id", (req, res) => {
  const query = db("users").where("id", req.params.id);
  query.then((results) => res.json(results));
});
```

### 2.2 XSS防护

**❌ 易受攻击的代码：**

```javascript
// 直接渲染用户输入
app.get("/api/posts/:id", (req, res) => {
  const post = getPost(req.params.id);
  res.send(`<h1>${post.title}</h1><p>${post.content}</p>`);
});

// 攻击示例：post.content = "<img src=x onerror='alert(1)'>"
// 结果：执行恶意JavaScript
```

**✅ 安全的代码：**

```javascript
// 方案1：HTML转义
const escapeHtml = (text) => {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
};

app.get("/api/posts/:id", (req, res) => {
  const post = getPost(req.params.id);
  res.send(
    `<h1>${escapeHtml(post.title)}</h1><p>${escapeHtml(post.content)}</p>`,
  );
});

// 方案2：使用模板引擎（自动转义）
app.get("/api/posts/:id", (req, res) => {
  const post = getPost(req.params.id);
  res.render("post", { post }); // 模板引擎自动转义
});

// 方案3：返回JSON而非HTML
app.get("/api/posts/:id", (req, res) => {
  const post = getPost(req.params.id);
  res.json(post); // 客户端负责转义
});
```

### 2.3 请求验证

```javascript
const { body, param, query, validationResult } = require("express-validator");

// 创建用户
app.post(
  "/api/users",
  [
    body("email").isEmail().normalizeEmail().withMessage("Invalid email"),
    body("password")
      .isLength({ min: 8 })
      .matches(/[A-Z]/)
      .matches(/[0-9]/)
      .withMessage(
        "Password must be at least 8 chars with uppercase and number",
      ),
    body("age")
      .isInt({ min: 0, max: 150 })
      .withMessage("Age must be between 0 and 150"),
    body("bio")
      .trim()
      .escape()
      .isLength({ max: 500 })
      .withMessage("Bio must be less than 500 characters"),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // 处理请求
    createUser(req.body);
  },
);

// 获取用户
app.get(
  "/api/users/:id",
  [param("id").isInt().withMessage("User ID must be an integer")],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const user = getUser(req.params.id);
    res.json(user);
  },
);

// 搜索用户
app.get(
  "/api/users",
  [
    query("search")
      .optional()
      .trim()
      .escape()
      .isLength({ max: 100 })
      .withMessage("Search term must be less than 100 characters"),
    query("page")
      .optional()
      .isInt({ min: 1 })
      .withMessage("Page must be a positive integer"),
  ],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const users = searchUsers(req.query.search, req.query.page);
    res.json(users);
  },
);
```

### 2.4 文件上传安全

```javascript
const multer = require("multer");
const path = require("path");

// 配置文件上传
const upload = multer({
  // 限制文件大小
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB
  },

  // 文件过滤
  fileFilter: (req, file, cb) => {
    // 允许的文件类型
    const allowedMimes = ["image/jpeg", "image/png", "image/gif"];
    const allowedExts = [".jpg", ".jpeg", ".png", ".gif"];

    const ext = path.extname(file.originalname).toLowerCase();
    const mime = file.mimetype;

    if (!allowedMimes.includes(mime) || !allowedExts.includes(ext)) {
      return cb(new Error("Invalid file type"));
    }

    cb(null, true);
  },

  // 存储配置
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      cb(null, "/secure/uploads/"); // 不在Web根目录
    },
    filename: (req, file, cb) => {
      // 使用随机名称，避免路径遍历
      const randomName = crypto.randomBytes(16).toString("hex");
      const ext = path.extname(file.originalname);
      cb(null, `${randomName}${ext}`);
    },
  }),
});

// 使用
app.post("/api/upload", upload.single("file"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded" });
  }

  // 扫描病毒（可选）
  scanForVirus(req.file.path);

  res.json({
    message: "File uploaded successfully",
    filename: req.file.filename,
  });
});
```

---

## 3. 限流与DDoS防护

### 3.1 基于IP的限流

```javascript
const rateLimit = require("express-rate-limit");

// 通用限流
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 最多100个请求
  message: "Too many requests from this IP",
  standardHeaders: true, // 返回RateLimit-*头
  legacyHeaders: false, // 禁用X-RateLimit-*头
});

// 认证端点严格限流
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 15分钟内最多5次尝试
  skipSuccessfulRequests: true, // 成功请求不计数
  message: "Too many login attempts",
});

// 应用限流
app.use("/api/", limiter);
app.post("/api/auth/login", authLimiter, loginHandler);
app.post("/api/auth/register", authLimiter, registerHandler);
```

### 3.2 分布式限流（Redis）

```javascript
const RedisStore = require("rate-limit-redis");
const redis = require("redis");
const client = redis.createClient();

const limiter = rateLimit({
  store: new RedisStore({
    client: client,
    prefix: "rl:", // 限流键前缀
    sendCommand: async (cmd, args) => {
      return client.sendCommand([cmd, ...args]);
    },
  }),
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
});

app.use("/api/", limiter);
```

### 3.3 基于用户的限流

```javascript
const rateLimit = require("express-rate-limit");

// 基于用户ID的限流
const userLimiter = rateLimit({
  keyGenerator: (req, res) => {
    // 已认证用户使用用户ID，未认证使用IP
    return req.user ? req.user.id : req.ip;
  },
  windowMs: 60 * 60 * 1000, // 1小时
  max: (req, res) => {
    // 不同用户等级有不同限制
    if (req.user && req.user.isPremium) {
      return 1000;
    }
    return 100;
  },
  message: "Rate limit exceeded",
});

app.use("/api/", userLimiter);
```

### 3.4 限流响应头

```javascript
// 标准限流响应头
app.use((req, res, next) => {
  res.setHeader("RateLimit-Limit", "100");
  res.setHeader("RateLimit-Remaining", "99");
  res.setHeader("RateLimit-Reset", Math.ceil(Date.now() / 1000) + 900);
  next();
});

// 客户端可根据这些头调整请求速率
```

---

## 4. 数据保护

### 4.1 传输加密（HTTPS/TLS）

```javascript
const https = require("https");
const fs = require("fs");

const options = {
  key: fs.readFileSync("private-key.pem"),
  cert: fs.readFileSync("certificate.pem"),
  // 强制TLS 1.2+
  minVersion: "TLSv1.2",
};

https.createServer(options, app).listen(443);

// 重定向HTTP到HTTPS
app.use((req, res, next) => {
  if (req.header("x-forwarded-proto") !== "https") {
    res.redirect(`https://${req.header("host")}${req.url}`);
  } else {
    next();
  }
});
```

### 4.2 静态数据加密

```javascript
const crypto = require("crypto");

// 加密敏感字段
function encryptField(plaintext, encryptionKey) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(
    "aes-256-cbc",
    Buffer.from(encryptionKey),
    iv,
  );

  let encrypted = cipher.update(plaintext, "utf8", "hex");
  encrypted += cipher.final("hex");

  return iv.toString("hex") + ":" + encrypted;
}

// 解密敏感字段
function decryptField(encryptedData, encryptionKey) {
  const [iv, encrypted] = encryptedData.split(":");
  const decipher = crypto.createDecipheriv(
    "aes-256-cbc",
    Buffer.from(encryptionKey),
    Buffer.from(iv, "hex"),
  );

  let decrypted = decipher.update(encrypted, "hex", "utf8");
  decrypted += decipher.final("utf8");

  return decrypted;
}

// 使用
const encryptionKey = crypto.scryptSync(
  process.env.ENCRYPTION_PASSWORD,
  "salt",
  32,
);

// 保存时加密
user.ssn = encryptField(user.ssn, encryptionKey);
await user.save();

// 读取时解密
user.ssn = decryptField(user.ssn, encryptionKey);
```

### 4.3 密码哈希

```javascript
const bcrypt = require("bcrypt");

// 注册时哈希密码
app.post("/api/auth/register", async (req, res) => {
  const { email, password } = req.body;

  // 验证密码强度
  if (!isStrongPassword(password)) {
    return res.status(400).json({ error: "Password too weak" });
  }

  // 哈希密码（盐轮数至少10）
  const passwordHash = await bcrypt.hash(password, 12);

  const user = await User.create({
    email,
    passwordHash,
  });

  res.json({ message: "User created successfully" });
});

// 登录时验证密码
app.post("/api/auth/login", async (req, res) => {
  const { email, password } = req.body;

  const user = await User.findOne({ email });
  if (!user) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  // 比较密码
  const isValid = await bcrypt.compare(password, user.passwordHash);
  if (!isValid) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const token = generateAccessToken(user);
  res.json({ token });
});

// 密码强度检查
function isStrongPassword(password) {
  return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(
    password,
  );
}
```

---

## 5. 安全响应头

```javascript
const helmet = require("helmet");

// 使用Helmet设置安全头
app.use(helmet());

// 或手动配置
app.use((req, res, next) => {
  // 防点击劫持
  res.setHeader("X-Frame-Options", "DENY");

  // 防MIME类型嗅探
  res.setHeader("X-Content-Type-Options", "nosniff");

  // 启用XSS防护
  res.setHeader("X-XSS-Protection", "1; mode=block");

  // 内容安全策略
  res.setHeader(
    "Content-Security-Policy",
    "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline' https://cdn.example.com; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data: https:; " +
      "font-src 'self' data:; " +
      "connect-src 'self' https://api.example.com; " +
      "frame-ancestors 'none'; " +
      "base-uri 'self'; " +
      "form-action 'self'",
  );

  // 严格传输安全
  res.setHeader(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains; preload",
  );

  // 引用策略
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");

  // 权限策略
  res.setHeader(
    "Permissions-Policy",
    "geolocation=(), microphone=(), camera=()",
  );

  next();
});
```

---

## 6. 错误处理与信息泄露防护

### 6.1 安全的错误响应

```javascript
// ❌ 错误做法：泄露系统信息
app.get("/api/users/:id", (req, res) => {
  try {
    const user = getUser(req.params.id);
    res.json(user);
  } catch (err) {
    res.status(500).json({
      error: err.message,
      stack: err.stack,
      query: err.query, // 可能包含敏感信息
    });
  }
});

// ✅ 正确做法：通用错误消息
app.get("/api/users/:id", (req, res) => {
  try {
    const user = getUser(req.params.id);
    res.json(user);
  } catch (err) {
    // 记录详细错误到日志
    logger.error("Error fetching user", {
      userId: req.params.id,
      error: err.message,
      stack: err.stack,
    });

    // 返回通用错误消息
    res.status(500).json({
      error: "An error occurred",
      requestId: req.id, // 便于追踪
    });
  }
});
```

### 6.2 错误处理中间件

```javascript
// 全局错误处理
app.use((err, req, res, next) => {
  // 记录错误
  logger.error("Unhandled error", {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    userId: req.user?.id,
  });

  // 确定HTTP状态码
  const statusCode = err.statusCode || 500;

  // 返回安全的错误响应
  res.status(statusCode).json({
    error: statusCode === 500 ? "Internal server error" : err.message,
    requestId: req.id,
  });
});
```

---

## 7. API安全审查清单

- [ ] 所有端点都实现了身份认证
- [ ] 所有端点都实现了授权检查
- [ ] 使用HTTPS/TLS加密所有通信
- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询防止SQL注入
- [ ] 所有输出都经过转义防止XSS
- [ ] 实现了限流和DDoS防护
- [ ] 敏感数据加密存储
- [ ] 密码使用bcrypt哈希（盐轮数≥10）
- [ ] 实现了安全的会话管理
- [ ] 错误消息不泄露系统信息
- [ ] 设置了安全响应头
- [ ] 实现了审计日志
- [ ] 依赖库无已知漏洞
- [ ] 进行了安全测试和渗透测试

---

## 参考资源

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
