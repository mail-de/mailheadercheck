-- Echo that the test is starting
mt.echo("*** begin test-02 - 1 From, 0 Subject, 0 Date")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/config.yaml")
conn = mt.connect("inet:40000@127.0.0.1", 50, 0.1)
if conn == nil then
     error "mt.connect() failed (timeout waiting for filter to start)"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_CONNECT, "i", "test-id")
if mt.mailfrom(conn, "mailer-daemon@example.com") ~= nil then
     error "mt.mailfrom() failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.mailfrom() unexpected reply"
end

-- send headers
if mt.header(conn, "From", "\"Test\" <test@example.com>") ~= nil then
     error "mt.header(From) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(From) unexpected reply"
end
if mt.header(conn, "Message-ID", "<1234@local.machine.example>") ~= nil then
     error "mt.header(Message-ID) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Message-ID) unexpected reply"
end
-- send EOM
if mt.eom(conn) ~= nil then
     error "mt.eom() failed"
end
if mt.getreply(conn) ~= SMFIR_REPLYCODE then
     error "mt.eom() unexpected reply"
end

-- wrap it up!
mt.disconnect(conn)
mt.signal(9)  -- we want to kill the milter quickly, otherwise each test takes 2-3 seconds to finish
