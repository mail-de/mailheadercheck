-- Echo that the test is starting
mt.echo("*** begin test-100 - From with multiple addresses, but check has enabled=0 (ACCEPT)")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-100-config.yaml")
conn = mt.connect("inet:40000@127.0.0.1", 50, 0.1)
if conn == nil then
     error "mt.connect() failed (timeout waiting for filter to start)"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_CONNECT, "i", "test-id-100")
if mt.mailfrom(conn, "sender@example.com") ~= nil then
     error "mt.mailfrom() failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.mailfrom() unexpected reply"
end

-- send headers (multiple addresses in From: would normally trigger not_exactly_one_address_in_from_header)
if mt.header(conn, "From", "\"User One\" <user1@example.com>, \"User Two\" <user2@example.com>") ~= nil then
     error "mt.header(From) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(From) unexpected reply"
end
if mt.header(conn, "Date", "Wed, 23 Jun 2021 16:30:55 +0200") ~= nil then
     error "mt.header(Date) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Date) unexpected reply"
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
if mt.getreply(conn) ~= SMFIR_ACCEPT then
     error "mt.eom() unexpected reply"
end

-- wrap it up!
mt.disconnect(conn)
mt.signal(9)  -- we want to kill the milter quickly, otherwise each test takes 2-3 seconds to finish
