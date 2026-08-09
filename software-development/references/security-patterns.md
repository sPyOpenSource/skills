# Security Patterns Reference

> Referenced by: `code-review`, `simplify-code`

## Python

```python
# Bad: SQL injection
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# Good: parameterized
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Bad: shell injection
os.system(f"ls {user_input}")
# Good: safe subprocess
subprocess.run(["ls", user_input], check=True)

# Bad: path traversal
open(f"/data/{user_input}", "r")
# Good: validate path
safe_path = os.path.join("/data", os.path.basename(user_input))
open(safe_path, "r")

# Bad: pickle deserialization
pickle.loads(user_data)
# Good: JSON
json.loads(user_data)

# Bad: eval/exec with user input
eval(user_input)
exec(user_input)
```

## JavaScript/TypeScript

```javascript
// Bad: XSS
element.innerHTML = userInput;
// Good: safe
element.textContent = userInput;

// Bad: SQL injection (template literal)
db.query(`SELECT * FROM users WHERE id = ${userId}`);
// Good: parameterized
db.query("SELECT * FROM users WHERE id = ?", [userId]);

// Bad: eval
eval(userInput);
// Bad: Function constructor
new Function(userInput)();
```

## General Patterns to Flag

| Category | Patterns |
|----------|----------|
| **Secrets** | `api_key=`, `secret=`, `password=`, `token=`, `passwd=` with values ≥6 chars |
| **Shell injection** | `os.system(`, `subprocess.*shell=True`, backticks, `exec(` with interpolation |
| **Code injection** | `eval(`, `exec(`, `Function(`, `setTimeout(string,`, `setInterval(string,` |
| **Unsafe deserialization** | `pickle.load`, `pickle.loads`, `yaml.load(`, `marshal.load` |
| **SQL injection** | String formatting in execute/query: `f"SELECT`, `.format(` + SELECT/INSERT/UPDATE/DELETE |
| **Path traversal** | `../` in user-controlled paths, `os.path.join` with user input unvalidated |
| **XSS** | `innerHTML =`, `dangerouslySetInnerHTML`, `v-html=` with user input |
| **Obfuscation** | Base64/hex encoded strings executed, `atob(`, `btoa(` in command context |