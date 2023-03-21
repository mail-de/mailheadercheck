-- Echo that the test is starting
mt.echo("*** begin test-85 - Is 'X-MailHeaderCheck' header added if config has 'add_result_header: 1'")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-85-config.yaml")
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
if mt.header(conn, "From", "\"Test\" <test@example.net>") ~= nil then
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
-- send EOM
if mt.eom(conn) ~= nil then
     error "mt.eom() failed"
end
-- verify that the "X-MailHeaderCheck" header field has been added
if not mt.eom_check(conn, MT_HDRADD, "X-MailHeaderCheck") then
     error "header X-MailHeaderCheck NOT added"
end

if mt.getreply(conn) ~= SMFIR_ACCEPT then
     error "mt.eom() unexpected reply"
end

-- wrap it up!
mt.disconnect(conn)
