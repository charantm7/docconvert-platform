local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2]) -- tokens per second
local now = tonumber(ARGV[3])

local data = redis.call("HMGET", key, "tokens", "timestamp")

local tokens = tonumber(data[1])
local last_time = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_time = now
end

-- refill tokens
local delta = math.max(0, now - last_time)
local refill = delta * refill_rate
tokens = math.min(capacity, tokens + refill)

if tokens < 1 then
    return 0
end

tokens = tokens - 1

redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
redis.call("EXPIRE", key, 3600)

return 1