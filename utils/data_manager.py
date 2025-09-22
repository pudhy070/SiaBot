import os
import json
from collections import defaultdict

base_path = r"D:\DiscordBot\json" # 경로 수정
os.makedirs(base_path, exist_ok=True)
ANNOUNCEMENT_CHANNELS_FILE = os.path.join(base_path, 'announcement_channels.json')
REPORTED_USERS_FILE = os.path.join(base_path, "reported_users.json")
TTS_CHANNELS_FILE = os.path.join(base_path, "tts_channels.json")
AUTOROLE_FILE = os.path.join(base_path, "autorole.json")
VRCHAT_PROFILES_FILE = os.path.join(base_path, "vrchat_profiles.json")
VRCHAT_CONFIG_FILE = os.path.join(base_path, "vrchat_config.json")
AI_CONFIG_FILE = os.path.join(base_path, "ai_config.json")

INVITE_LINKS_FILE = os.path.join(base_path, "invite_links.json")

INVITE_LINKS = {}


def save_json(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if isinstance(data, defaultdict):
            data = dict(data)
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 ({filepath}): {e}")

def save_invite_links():
    save_json(INVITE_LINKS_FILE, INVITE_LINKS)

def load_json(filepath, default_factory=dict):
    if not os.path.exists(filepath):
        return default_factory() if callable(default_factory) else default_factory
    try:
        with open(filepath, "r", encoding='utf-8') as f:
            content = f.read()
            if not content:
                return default_factory() if callable(default_factory) else default_factory
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_factory() if callable(default_factory) else default_factory


def load_all_data(bot):
    global INVITE_LINKS

    reported_data = load_json(REPORTED_USERS_FILE, lambda: {})
    bot.reported_users = defaultdict(lambda: {'count': 0, 'reasons': []}, reported_data)

    announcement_data = load_json(ANNOUNCEMENT_CHANNELS_FILE, lambda: {})
    bot.announcement_channels = {int(k): v for k, v in announcement_data.items()}

    bot.tts_channels = load_json(TTS_CHANNELS_FILE, dict)
    bot.autorole_config = load_json(AUTOROLE_FILE, dict)
    bot.vrchat_profiles = load_json(VRCHAT_PROFILES_FILE, dict)
    bot.vrchat_config = load_json(VRCHAT_CONFIG_FILE, dict)
    bot.ai_config = load_json(AI_CONFIG_FILE, dict)

    loaded_invites = load_json(INVITE_LINKS_FILE, dict)
    INVITE_LINKS.update(loaded_invites)
    print(f"✅ {len(INVITE_LINKS)}개의 서버 초대 링크 로드 완료.")
    
    print("모든 데이터 로드 완료.")
# --- 피싱 URL 데이터베이스 ---
PHISHING_URLS = [
    "evil-site.com", "free-nitro.xyz", "discord-gift.click", "steamcomminity.com", "discorb.gg",
    "discord-nltro.com", "discord-gifts.top", "dlscord.co", "discord-app.info", "discord-verify.online",
    "nitro-giveaway.fun", "cliscord.com", "dlscord-login.pw", "steancommunity.com", "steam-power.xyz",
    "stearncomunity.ru", "csgo-skins-free.shop", "steamuser.club", "valve-secure.link", "google-support.website",
    "microsoft-account.org", "paypal-security.click", "amazon-update.biz", "apple-id-verify.site", "secure-login.online",
    "web-auth.info", "login-secure.me", "your-prize-claim.com", "lucky-winner.io", "free-rewards.net",
    "event-claim.co", "bonus-cash.xyz", "account-security-discord.com", "verify-steam-profile.net", "login-google-apps.info",
    "update-microsoft-licence.org", "customer-support-paypal.live", "discourd.xyz", "steamscomunity.me", "gooogle.biz",
    "paypall.click", "amazonn.shop", "free-skins-csgo.xyz", "nitro-claim-event.online", "giftcard-redeem.club",
    "activation-code.site", "human-verification.pw", "click-here-to-login.com", "verify-your-identity.cc",
    "security-alert-notification.info", "urgent-message-read.net", "account-locked-fix.xyz",
    "discord-security-service.com", "steam-community-login-secure.xyz", "verify-your-acccount-now.net",
    "update-microsoft-profile-id.org", "xfer-money-confirm.click", "discord-users.info", "steam-verify.site",
    "google-email-recovery.me", "roblox-free-robux.fun", "nintendo-eshop-redeem.shop", "crypto-wallet-connect.link",
    "nft-airdrop-claim.xyz", "valorant-free-skins.top", "discordv2.com", "steam-client-v3.online",
    "google-auth2025.info", "dropbox-sync-file.biz", "onedrive-share-document.click", "dis.gg", "st.cc", "go.xyz",
    "outlook-verify-email.online", "gmail-account-sync.top", "facebook-password-reset.info", "instagram-profile-verify.link",
    "telegram-channel-join.xyz", "whatsapp-security-code.club", "bank-of-america-alert.website", "wells-fargo-secure-login.net",
    "visa-transaction-review.org", "mastercard-fraud-alert.co", "creditunion-notice.online", "fintech-wallet-connect.app",
    "ups-delivery-tracking.info", "fedex-package-hold.click",
    "irs-tax-refund.top", "gov-support-program.online", "police-ticket-payment.info", "health-department-covid.xyz",
    "windows-update-critical.net", "adobe-flash-security.link", "antivirus-threat-detected.club", "system-error-fix.website",
    "epicgames-free-vbucks.fun", "blizzard-account-lock.info", "riotgames-verify-account.click", "game-key-generator.xyz",
    "minecraft-server-status.top", "data-breach-notification.online", "privacy-policy-update.info", "terms-of-service-change.link",
    "dlsçord.com", "stęam.com", "googlè.com", "nltro-frëe.xyz", "paypal-auth✅.info", "discord-support-ᗯ.com",
    "discord-official.site", "steam-secure-login.info", "google-account-recovery.top", "microsoft-online-portal.net", "paypal-limited-access.org",
    "irs.gov-support.online", "student-loan-edu.link", "us-treasury.info",
    "fortnite-vbucks-generator.club", "valorant-points-free.xyz", "genshin-impact-codes.fun", "roblox-account-upgrade.online",
    "apex-legends-free-coins.site", "fifa-ultimate-team-rewards.top", "leagueoflegends-riotid-verify.info",
    "pubg-mobile-uc-free.net", "twitch-prime-rewards.click", "youtube-monetization-alert.biz",
    "ebay-payment-hold.online", "aliexpress-order-status.info", "shopify-store-verification.site", "stripe-payment-review.link",
    "azure-login-portal.net", "aws-billing-notification.top", "slack-workspace-invite.xyz", "notion-shared-page.click",
    "zoom-meeting-recordings.info", "security-breach-alert.website", "data-privacy-notification.online",
    "identity-theft-prevention.info", "phishing-attempt-detected.link", "cyber-attack-report.xyz",
    "discord-maintenance-update.net", "steam-server-offline.top", "google-account-suspended.online",
    "microsoft-outlook-error.site", "paypal-fraudulent-activity.info", "secure-verify.com",
    "account-center.net", "web-portal.info", "client-dashboard.online", "my-profile-update.xyz",
    "disxord.gg", "dscord.com", "dlsocord.info", "discordapp.xyz", "disrcord.online",
    "nltro-glfts.fun", "free-nlto.shop", "nitro-boost-giveaway.club", "discord-help-desk.site",
    "discord-security-team.net", "disc0rd.com", "dlscords.gg", "discord-claim.top",
    "stermcomunity.com", "steammunity.info", "staeam.net", "steam-rewards.xyz",
    "valve-steam-support.online", "steam-communnity.biz", "csgo-trade-offers.link",
    "pubg-skins-free.website", "dota2-item-claim.top",
    "googel.com.co", "microsft.net", "appl-support.org", "amzon.shop",
    "office365-login.site", "google-drive-share.online", "icloud-data-sync.info",
    "microsoft-outlook-web.top", "amazon-prime-verify.link",
    "bitcoin-wallet-sync.xyz", "ethereum-giveaway.fun", "binance-security-check.club",
    "coinbase-verify-account.net", "crypto-exchange-update.online",
    "trading-platform-login.info", "investment-fund-rewards.website",
    "delivery-tracking-status.com", "parcel-delivery-alert.net", "ecommerce-order-issue.top",
    "shopping-rewards-claim.xyz", "your-order-shipping.info",
    "twitter-account-suspended.site", "tiktok-bonus-coins.online", "snapchat-verify-profile.link",
    "facebook-messenger-update.info", "linkedin-job-offer.club",
    "playstation-network-error.net", "xbox-live-rewards.xyz", "nintendo-support-ticket.online",
    "ea-sports-promo.top", "ubisoft-connect-login.info", "epicgames-refund-request.website",
    "aliexpress-refund-center.com", "lazada-order-problem.net", "shopee-voucher-claim.online",
    "gmarket-special-offer.top", "11st-discount-coupon.xyz",
    "system-security-alert.info", "malware-detected-warning.online", "server-maintenance-notice.link",
    "critical-patch-update.top", "windows-defender-scan.website", "mac-os-update-required.net",
    "firewall-protection-error.club", "browser-security-check.xyz",
    "login-securely.com", "verify-portal.net", "account-service.info", "official-support.online",
    "client-area.xyz", "web-access.top", "data-center.link", "help-centre.website",
    "dashboard-access.club", "secure-gateway.net", "email-confirmation.info",
    "password-recovery-form.online", "payment-verification.top", "transaction-alert.xyz",
    "security-audit.link", "urgent-action-required.website", "notification-center.club",
    "your-profile-update.info", "system-notification.online", "service-upgrade.top",


    # 정부 기관/세무/법무 관련 (글로벌 기준)
    "federal-tax-audit.online",
    "justice-department-notice.info",
    "homeland-security-alert.website",
    "national-crime-agency.top", # 영국 NCA 사칭
    "interpol-warning.xyz",
    "europol-security-check.link",
    "customs-border-protection.net",
    "department-of-justice-verify.site",
    "social-security-administration.club", # 미국 SSA 사칭
    "immigration-status-update.online",
    "court-summons-notification.info",
    "government-aid-program.website",
    "official-census-data.top",
    "voter-registration-update.xyz",
    "public-service-portal.link",

    # 보건/의료/팬데믹 관련
    "who-health-alert.online", # WHO 사칭
    "cdc-covid-update.info", # 미국 CDC 사칭
    "nih-research-portal.website", # 미국 NIH 사칭
    "ministry-of-health-notice.top",
    "disease-control-center.xyz",
    "public-health-advisory.link",

    # 국방/정보/보안 관련
    "cia-security-breach.online", # 미국 CIA 사칭
    "fbi-cyber-crime.info", # 미국 FBI 사칭
    "nsa-data-security.website", # 미국 NSA 사칭
    "mod-military-update.top", # 영국 MoD 사칭
    "defence-intelligence-agency.xyz", # DIA 사칭
    "secure-national-intelligence.link",

    # 기타 공공 서비스/인프라 사칭
    "electric-grid-maintenance.online",
    "water-utility-bill.info",
    "public-transport-notice.website",
    "city-council-announcement.top",
    "environmental-agency-report.xyz",
    "postal-service-redirect.link"

    # 정부 포털/서비스 사칭 
    "gov24-korea.online",
    "korea-gov-portal.info",
    "korea-citizen-alert.website",
    "national-e-government.top",
    "korean-gov-support.xyz",
    "minwon24-verify.link", 

    # 국세청/세금 관련 사칭
    "nts-korea-tax.com", #
    "korea-tax-refund.net",
    "tax-payment-update.online",
    "korea-revenue-service.info",
    "hts-korea.website", 
    "tax-notification-kr.top",

    # 경찰청/법원/검찰청 사칭
    "korea-police-notice.online",
    "cyber-police-korea.info",
    "korea-court-summons.website",
    "public-prosecutor-kr.top",
    "traffic-violation-kr.xyz",
    "criminal-investigation-kr.link",

    # 국민건강보험공단/국민연금공단 사칭
    "nhis-korea-checkup.com",
    "korea-health-insur.net",
    "nps-korea-pension.online", 
    "korea-welfare-benefit.info",
    "health-insurance-alert.website",
    "pension-service-kr.top",

    # 질병관리청/보건복지부 사칭
    "kdca-korea-info.com", 
    "korea-health-covid.net",
    "mohw-korea-notify.online",
    "public-health-korea.info",
    "vaccine-appointment-kr.website",

    # 병무청 사칭
    "mma-korea-duty.com", 
    "military-service-kr.net",
    "conscription-office-kr.online",

    # 병역판정검사 등
    "korea-medical-exam.info",

    # 고용노동부/산업인력공단 사칭
    "moel-korea-labor.com", 
    "hrdkorea-skill-test.net", 
    "employment-support-kr.online",

    # 관세청/법무부 등
    "korea-customs-duty.info",
    "ministry-of-justice-kr.website",

    # 기타 정부기관/공공 서비스 사칭
    "korea-statistics-info.com",
    "korea-fire-safety.net",
    "e-cops-verify.online", 
    "korea-electric-power.info",
    "korea-water-utility.website",
    "korea-post-tracking.top",
    "child-care-support-kr.xyz", 
    "environmental-agency-kr.link"
]
URL_REGEX = r"(?P<url>https?:\/\/[^\s]+)"