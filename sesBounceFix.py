# Python 2.7
from __future__ import print_function
from base64 import b64decode

import os, json, boto3, urllib2, base64

## Environment variables
# You can define Environment Variables as key-value pairs that are accessible from your function code.
jenkins_url = os.environ['jenkins_url'] # plaintext
enc_username = os.environ['username'] # encrypted with KMS key
enc_password = os.environ['password'] # encrypted with KMS key


# Calls Jenkins job to fix bounced email address in database
def callJenkins(email):
    print("Calling Jenkins _fix_email_bounce ( " + email + " ) ...")
    try:
        # Connect to Jenkins and build a job
        strUrl = jenkins_url + "/job/_fix_email_bounce/buildWithParameters?token=f90416498a64&Replace=true&email=" + email
        print(strUrl)
        request = urllib2.Request(strUrl)

        username = boto3.client('kms').decrypt(CiphertextBlob=b64decode(enc_username))['Plaintext']
        password = boto3.client('kms').decrypt(CiphertextBlob=b64decode(enc_password))['Plaintext']
        #base64string = base64.encodestring('%s:%s' % ('username', 'password')).replace('\n', '')
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
    except Exception as e:
        print(e)
        print('Cannot connect to Jenkins server or run build job')
        raise e


# Gets notifications from SNS topic ses_email_bounces and parses it for an email
def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    message = event['Records'][0]['Sns']['Message']
    message = json.loads(message)

    # message is dict
    if 'bounce' in message:
        bounce = message['bounce']

        # bounce is dict
        if 'bouncedRecipients' in bounce:
            bouncedRecipients = bounce['bouncedRecipients']

            if len(bouncedRecipients) > 0:
                for bouncedRecipient in bouncedRecipients:
                    email = bouncedRecipient['emailAddress']
                    print("SNS email: " , email)
                    callJenkins(email)
        return "another job well done :-)"
    else:
        return "doesn't look like a geniune bounce AWS Notification to me :-/"

