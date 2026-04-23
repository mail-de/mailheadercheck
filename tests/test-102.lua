-- Echo that the test is starting
mt.echo("*** begin test-102 - Malformed CIDR in exclude_ips: ValueError must be caught, check still runs (REJECT)")

-- start the filter
mt.startfilter("./mailheadercheck", "--config", "tests/test-102-config.yaml")
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

-- send headers (no From header — triggers missing_from_header)
if mt.header(conn, "Subject", "Test") ~= nil then
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
if mt.header(conn, "Message-ID", "<1234@local.machine.example>") ~= nil then
     error "mt.header(Message-ID) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Message-ID) unexpected reply"
end
-- send EOM: malformed CIDR triggers ValueError in ip_found_in_exclude_ip_list,
-- which must be caught so the check still runs and rejects the message
if mt.eom(conn) ~= nil then
     error "mt.eom() failed"
end
if mt.getreply(conn) ~= SMFIR_REPLYCODE then
     error "mt.eom() unexpected reply"
end

-- wrap it up!
mt.disconnect(conn)
mt.signal(9)  -- we want to kill the milter quickly, otherwise each test takes 2-3 seconds to finish
