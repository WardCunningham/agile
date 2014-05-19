#!/home/ward/ruby/bin/ruby

require "cgi"
require 'net/smtp'
require "agile"

cgi = CGI.new("html3")

FROM_EMAIL = "signers@AgileManifesto.org"

class CGI

def field(name)
self[name][0] || ""
end

def given(name)
value = field(name)
value = value.strip
value = nil if value.length.zero?
value
end
end

def pline(left, right)
%{<li><font size="-1"><b>#{left}</b> over #{right}</font>
}
end

def principles
"<ul>\n" +
pline("Individuals and interactions", "processes and tools") +
pline("Working software", "comprehensive documentation") +
pline("Customer collaboration", "contract negotiation") +
pline("Responding to change", "following a plan") +
"</ul>\n"
end


def display_form(cgi)
cgi.instance_eval {
form("method" => "post") {
table {
tr {
  td { "Name:" } +
    td { input('name' => 'name', 'value' => field('name')) }
} +
  tr {
  td { "E-Mail:" } +
    td { input('name' => 'email', 'value' => field('email')) }
} +
  tr {
  td {} +
    td { checkbox('name' => "publish_email",
		  'checked' => field('publish_email') == "on") + 
      "&nbsp;add my e-mail address as a link from my name" }
} +
tr {
  td { "Organization:" } +
    td { input('name' => 'org', 'value' => field('org'))  +
      font('size' => "-2") { "(optional)" } }
} +
  tr {
  td { "URL:" } +
    td { text_field('name' => 'url', 'value' => field('url'))  +
      font('size' => "-2") { "(optional)" } }
} +
  tr {
  td { "Endorsement:" } +
    td { textarea('comment', 45, 12) { field('comment') }+
      font('size' => "-2") { "(optional)" } }
} +
  tr {
  td { "Action:" } +
    td { submit("Preview", "action") + "&nbsp;&nbsp" + submit("Submit", "action") }
}
}
}
}
end


def std_page(cgi, body)
cgi.out {
cgi.html {
cgi.head { cgi.title { "Agile Manifesto Signatories" } } +
cgi.body('background' => "/background.jpg") { body }
}
}
end


def main_form(cgi, support_msg, note)
body = '<center>
  <table width="80%">
    <tr colspan="2"><td>
      <h2>I Support the Agile Manifesto!</h2>
    </td></tr>
    <tr><td width="65%" valign="top">
  '
body << note << "<p>"
body << display_form(cgi) 
body << '<p><font size="-1">

<b>Privacy policy:</b> We need your e-mail
address in order to send you a validation message. When you
respond to that message, we\'ll be able to add your name and
comments to the list. If you have clicked <i>Add e-mail as
hyperlink to my name</i>, we\'ll also make your name a hyperlink
to your e-mail address. We will not use your e-mail address in
any other way. Similarly, you may choose to give us a URL for a 
web page. If so, we\'ll add it as a hyperlink to your organization\'s
name when we display it. We will make no other use of
this information.

<p><b>Review policy:</b> We review every signature.
When an endorsement is included we expect it to endorse the manifesto,
not some other method, company or person.
We don\'t post comments containing html or additional urls,
nor do we often respond to comments or inquiries.

</td><td width="35%" valign="top">
<p><font size="-1">
We are uncovering better ways of developing
software by doing it and helping others do it.
Through this work we have come to value:</font><br>
'
body << principles

body << '<font size="-1">That is, while there is value in the items on
the right, we value the items on the left more.</font><br>
'

if support_msg
body << "<p><hr><p><b>Your support message will look something like:</b>\n" 
body << "<p><table width=\"100%\" bgcolor=\"#ddeecc\" border=4 cellpadding=8><tr><td>"
body << "<p><hr>" << support_msg.to_html << "<hr><p></td></tr></table>"
end

body << '</td></tr></table></center>'
body << '<script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
</script>
<script type="text/javascript">
_uacct = "UA-2377314-1";
urchinTracker();
</script>'

std_page(cgi, body)

end

def fail(cgi, msg)
main_form(cgi, nil, "<font color=\"red\"><b>#{msg}</b></font>")
exit
end


def validate(cgi)
fail(cgi, "Please enter your name") unless cgi.given("name")
fail(cgi, "Please enter your e-mail address") unless cgi.given("email")
end


def support_from_form(cgi)
return SupportMessage.new(cgi.field("name"),
		    cgi.field("email"),
		    cgi.field("publish_email") == "on",
		    cgi.field("org"),
		    cgi.field("url"),
		    cgi.field("comment"),
		    Time.now)
end


def send_email(msg_ref, message)
Net::SMTP.start('localhost') do |smtp|
smtp.ready(FROM_EMAIL, message.email) do |a|
a.write "Subject: Agile Manifesto Confirmation \##{msg_ref}\r\n"
a.write "Reply-to: #{FROM_EMAIL}\r\n"
      a.write "\r\n"
      a.write "You (or someone pretending to be you) recently signed the\r\n"
      a.write "Manifesto for Agile Software Development (described on the site\r\n"
      a.write "http://www.AgileManifesto.org. You wrote:\r\n\r\n"
      a.write message.to_email
      a.write "\r\nWe're sending this e-mail to confirm that you'd like\r\n"
      a.write "your signature added to our public signatories page. If so,\r\n"
      a.write "simply reply to this message without changing the subject line.\r\n"
    end
  end
end


def submit_form(cgi)
  body = "<center><table width=\"50%\"><tr><td>\n" +
   "<p>&nbsp;<p>Thank you for your support. We'll shortly be sending " +
    "you an e-mail asking you to confirm that you want this " +
    "message posted. When you respond, we'll add your message " +
    "to the list of supporters on the web site." +
    "<p>Agile Manifesto <a href=\"http://www.AgileManifesto.org\">home</a>." +
    "</td></tr></table>\n"

  std_page(cgi, body)
end


action = cgi.field("action")

note = "<b>Add your name</b> to the list of people signing the
           Agile Software Development Manifesto."

message = nil

if action.length > 0
  validate(cgi)
  message = support_from_form(cgi)

  if action == "Submit"
    dir = PendingDir.new
    if !message.spam?
      msg_ref = dir.add(message)
      send_email(msg_ref, message)
    end
    submit_form(cgi)
    exit
  else
    note = "<b>Your message of support is displayed on the right</b>"
  end

  
end

  
main_form(cgi, message, note)

