-- Echo that the test is starting
mt.echo("*** begin test-28 - Subject:-Header too long")

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
--if mt.header(conn, "Subject", "this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long-this-is-2016-chars-long") ~= nil then
if mt.header(conn, "Subject", "=?UTF-8?B?dGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE=?=\n =?UTF-8?B?Ni1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXM=?=\n =?UTF-8?B?LWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG8=?=\n =?UTF-8?B?bmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWM=?=\n =?UTF-8?B?aGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXM=?=\n =?UTF-8?B?LTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy0=?=\n =?UTF-8?B?dGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXI=?=\n =?UTF-8?B?cy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjA=?=\n =?UTF-8?B?MTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGk=?=\n =?UTF-8?B?cy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWw=?=\n =?UTF-8?B?b25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi0=?=\n =?UTF-8?B?Y2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWk=?=\n =?UTF-8?B?cy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmc=?=\n =?UTF-8?B?LXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGE=?=\n =?UTF-8?B?cnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTI=?=\n =?UTF-8?B?MDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGg=?=\n =?UTF-8?B?aXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy0=?=\n =?UTF-8?B?bG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTY=?=\n =?UTF-8?B?LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy0=?=\n =?UTF-8?B?aXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb24=?=\n =?UTF-8?B?Zy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2g=?=\n =?UTF-8?B?YXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0=?=\n =?UTF-8?B?MjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXQ=?=\n =?UTF-8?B?aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnM=?=\n =?UTF-8?B?LWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE=?=\n =?UTF-8?B?Ni1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXM=?=\n =?UTF-8?B?LWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG8=?=\n =?UTF-8?B?bmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWM=?=\n =?UTF-8?B?aGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXM=?=\n =?UTF-8?B?LTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy0=?=\n =?UTF-8?B?dGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXI=?=\n =?UTF-8?B?cy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjA=?=\n =?UTF-8?B?MTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGk=?=\n =?UTF-8?B?cy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWw=?=\n =?UTF-8?B?b25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi0=?=\n =?UTF-8?B?Y2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWk=?=\n =?UTF-8?B?cy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmc=?=\n =?UTF-8?B?LXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGE=?=\n =?UTF-8?B?cnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTI=?=\n =?UTF-8?B?MDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGg=?=\n =?UTF-8?B?aXMtaXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy0=?=\n =?UTF-8?B?bG9uZy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTY=?=\n =?UTF-8?B?LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy0=?=\n =?UTF-8?B?aXMtMjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb24=?=\n =?UTF-8?B?Zy10aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2g=?=\n =?UTF-8?B?YXJzLWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0=?=\n =?UTF-8?B?MjAxNi1jaGFycy1sb25nLXRoaXMtaXMtMjAxNi1jaGFycy1sb25nLXQ=?=\n =?UTF-8?B?aGlzLWlzLTIwMTYtY2hhcnMtbG9uZy10aGlzLWlzLTIwMTYtY2hhcnM=?=\n =?UTF-8?B?LWxvbmctdGhpcy1pcy0yMDE2LWNoYXJzLWxvbmctdGhpcy1pcy0yMDE=?=\n =?UTF-8?B?Ni1jaGFycy1sb25n?=") ~= nil then
     error "mt.header(Subject) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Subject) unexpected reply"
end
if mt.header(conn, "Date", "123") ~= nil then
     error "mt.header(Date) failed"
end
if mt.getreply(conn) ~= SMFIR_CONTINUE then
     error "mt.header(Date) unexpected reply"
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
