-- Echo that the test is starting
mt.echo("*** begin test-80 - 1 From, 0 Subject, 0 Date, log_json=1")

-- start the filter
mt.startfilter("./mailheadercheck", "--socket", "inet:40000@127.0.0.1", "--log_json=1")
mt.sleep(2)

-- try to connect to it
conn = mt.connect("inet:40000@127.0.0.1")
if conn == nil then
     error "mt.connect() failed"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_MAIL, "i", "test-id")
if mt.mailfrom(conn, "sender@test.example.com") ~= nil then
     error "mt.mailfrom() failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.mailfrom() unexpected reply"
end

-- send From-Header with "
if mt.header(conn, "From", "displayname with space, \"doublequotes\" and 'singlequotes' <sender@test.example.com>") ~= nil then
     error "mt.header(From) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(From) unexpected reply"
end
-- send EOH
if mt.eoh(conn) ~= nil then
     error "mt.eoh() failed"
end
if mt.getreply(conn) ~= SMFIR_REPLYCODE then
     error "mt.eoh() unexpected reply"
end

-- wrap it up!
mt.disconnect(conn)
