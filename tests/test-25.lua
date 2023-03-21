-- Echo that the test is starting
mt.echo("*** begin test-25 - more than one from address")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/config.yaml")
mt.sleep(2)

-- try to connect to it
conn = mt.connect("inet:40000@127.0.0.1")
if conn == nil then
     error "mt.connect() failed"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_MAIL, "i", "test-id")
if mt.mailfrom(conn, "test@example.com") ~= nil then
     error "mt.mailfrom() failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.mailfrom() unexpected reply"
end

-- send headers
if mt.header(conn, "From", "=?utf-8?B?Q2hyaXN0aWFuIFLDtsOfbmVy?= <test@example.com>, <second@example.com>") ~= nil then
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
