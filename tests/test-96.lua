-- Echo that the test is starting
mt.echo("*** begin test-96 - Missing Message-ID, Envelope-From in exclude_envelopefrom_addresses (ACCEPT)")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-96-config.yaml")
mt.sleep(2)

-- try to connect to it
conn = mt.connect("inet:40000@127.0.0.1")
if conn == nil then
     error "mt.connect() failed"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_CONNECT, "i", "test-id-96")
if mt.mailfrom(conn, "bounce@example.org") ~= nil then
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
