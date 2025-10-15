-- Echo that the test is starting
mt.echo("*** begin test-94 - Missing Message-ID, but From address in exclude_fromheader_addresses (ACCEPT)")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-94-config.yaml")
conn = mt.connect("inet:40000@127.0.0.1", 50, 0.1)
if conn == nil then
     error "mt.connect() failed (timeout waiting for filter to start)"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_CONNECT, "i", "test-id-94")
if mt.mailfrom(conn, "sender@example.com") ~= nil then
     error "mt.mailfrom() failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.mailfrom() unexpected reply"
end

-- send headers
if mt.header(conn, "From", "\"User\" <user@example.org>") ~= nil then
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
-- Do NOT send Message-ID on purpose

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
