-- Echo that the test is starting
mt.echo("*** begin test-98 - Missing Message-ID, SASL username in exclude_sasl_usernames (ACCEPT)")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-98-config.yaml")
mt.sleep(2)

-- try to connect to it
conn = mt.connect("inet:40000@127.0.0.1")
if conn == nil then
     error "mt.connect() failed"
end

-- send envelope macros and sender data
-- mt.helo() is called implicitly
mt.macro(conn, SMFIC_MAIL, "i", "test-id-98")
-- Provide SASL username via macros (both forms to maximize compatibility)
mt.macro(conn, SMFIC_MAIL, "auth_authen", "alice")
mt.macro(conn, SMFIC_MAIL, "{auth_authen}", "alice")
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
