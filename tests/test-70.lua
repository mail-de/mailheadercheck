-- Echo that the test is starting
mt.echo("*** begin test-70 - 1 From, 1 Subject, 1 Date, 2 References")

-- start the filter
mt.startfilter("./mailheadercheck", "--socket", "inet:40000@127.0.0.1")
mt.sleep(2)

-- try to connect to it
conn = mt.connect("inet:40000@127.0.0.1")
if conn == nil then
     error "mt.connect() failed"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_MAIL, "i", "test-id")
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
if mt.header(conn, "Subject", "Subject line 1") ~= nil then
     error "mt.header(Subject) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Subject) unexpected reply"
end
if mt.header(conn, "Date", "Wed, 23 Jun 2021 16:30:55 +0200") ~= nil then
     error "mt.header(Date) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Date) unexpected reply"
end
if mt.header(conn, "Cc", "Cc1 display name <cc1@example.com>") ~= nil then
     error "mt.header(Cc) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Cc) unexpected reply"
end
if mt.header(conn, "References", "<1234@local.machine.example>") ~= nil then
     error "mt.header(References) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(References) unexpected reply"
end
if mt.header(conn, "References", "<5678@second.messageid.example>") ~= nil then
     error "mt.header(References) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(References) unexpected reply"
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