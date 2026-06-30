import resend
from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY

def send_password_change_alert(user_email: str):
    """Sends a security alert via Resend when a password is changed."""
    html_content = """
        <div style="background-color: #e8e8e8; padding: 32px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 580px; margin: 0 auto;">
            <div style="background: #ffffff; border-radius: 4px; overflow: hidden;">

            <!-- Header -->
            <div style="background-color: #E8380D; padding: 28px 40px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 36px; height: 36px; background: rgba(255,255,255,0.15); border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <path d="M9 2L11.2 6.4L16 7.3L12.5 10.7L13.4 15.5L9 13.1L4.6 15.5L5.5 10.7L2 7.3L6.8 6.4L9 2Z" fill="rgba(255,255,255,0.9)" stroke="rgba(255,255,255,0.5)" stroke-width="0.5"/>
                </svg>
                </div>
                <p style="color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: 0.3px; margin: 0;">HeyScarlet</p>
            </div>

            <!-- Body -->
            <div style="padding: 40px 40px 32px;">

                <!-- Alert badge -->
                <div style="display: flex; align-items: center; gap: 10px; background: #FEF2F0; border: 1px solid #F5B8AC; border-radius: 4px; padding: 12px 16px; margin-bottom: 28px;">
                <span style="font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #C02B0A;">Security notification</span>
                </div>

                <h2 style="font-size: 21px; font-weight: 600; color: #111111; margin: 0 0 18px; line-height: 1.3;">Your password was changed</h2>

                <p style="font-size: 15px; line-height: 1.65; color: #444444; margin: 0 0 20px;">We're letting you know that the password on your HeyScarlet account was successfully updated. </p>

                <hr style="border: none; border-top: 1px solid #F0F0F0; margin: 24px 0;">

                <!-- Action callout -->
                <div style="background: #FEF2F0; border-left: 3px solid #E8380D; border-radius: 0 4px 4px 0; padding: 18px 20px; margin: 24px 0;">
                <p style="font-size: 13px; font-weight: 600; color: #C02B0A; margin: 0 0 6px;">Didn't make this change?</p>
                <p style="font-size: 13px; color: #7A2010; margin: 0 0 14px; line-height: 1.5;">If you don't recognise this activity, your account may be compromised. Secure it immediately by resetting your password, then reach out to our team.</p>
                <a href="mailto:support@heyscarlet.com" style="display: inline-block; background: #E8380D; color: #ffffff; font-size: 13px; font-weight: 600; padding: 9px 20px; border-radius: 4px; text-decoration: none; letter-spacing: 0.2px;">Secure my account</a>
                </div>

                <!-- Safe note -->
                <p style="font-size: 13px; color: #666666; margin: 20px 0 0; line-height: 1.6; padding: 14px 16px; background: #F8F8F8; border-radius: 4px;">
                If this was you, No worries! Your account is protected by your new password. For any questions, contact <a href="mailto:support@heyscarlet.com" style="color: #E8380D; text-decoration: none;">support@heyscarlet.com</a>.
                </p>

            </div>

            <!-- Footer -->
            <div style="background: #F7F7F7; border-top: 1px solid #EBEBEB; padding: 24px 40px;">
                <div style="margin-bottom: 14px;">
                <a href="#" style="font-size: 12px; color: #888888; text-decoration: none; margin-right: 20px;">Privacy Policy</a>
                <a href="#" style="font-size: 12px; color: #888888; text-decoration: none; margin-right: 20px;">Terms of Service</a>
                <a href="#" style="font-size: 12px; color: #888888; text-decoration: none;">Help Centre</a>
                </div>
                <p style="font-size: 11px; color: #AAAAAA; line-height: 1.6; margin: 0;">
                You received this because you have a <span style="color: #E8380D; font-weight: 600;">HeyScarlet</span> account. This is an automated security alert — please do not reply directly to this message.<br>
                &copy; 2026 HeyScarlet. All rights reserved.
                </p>
            </div>

            </div>
        </div>
        </div>
        """
    
    # Resend requires these specific keys to process the email
    params: resend.Emails.SendParams = {
        "from": "Security <onboarding@resend.dev>",
        # Testing emails Can only be sent to your resend email if you dont have a domain yet. so you can swap the var for your mail to test
        "to": ["nandomdrimz@gmail.com"], #[user_email], 
        "subject": "Your Password Has Been Changed",
        "html": html_content,
    }
    
    try:
        # Executes the API call to Resend
        resend.Emails.send(params) 
    except Exception as e:
        # this failure will be logged latercinstead of just printing
        print(f"Failed to send email alert: {e}")