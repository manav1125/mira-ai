BEGIN;

CREATE OR REPLACE FUNCTION public.cleanup_sensitive_integrations_on_account_delete()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, basejump
AS $$
BEGIN
    IF to_regclass('public.user_mcp_credential_profiles') IS NOT NULL THEN
        DELETE FROM public.user_mcp_credential_profiles
        WHERE account_id = OLD.id;
    END IF;

    IF to_regclass('public.user_mcp_credentials') IS NOT NULL THEN
        DELETE FROM public.user_mcp_credentials
        WHERE account_id = OLD.id;
    END IF;

    IF to_regclass('public.google_oauth_tokens') IS NOT NULL THEN
        DELETE FROM public.google_oauth_tokens
        WHERE user_id = OLD.primary_owner_user_id;
    END IF;

    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trigger_cleanup_sensitive_integrations_on_account_delete ON basejump.accounts;
CREATE TRIGGER trigger_cleanup_sensitive_integrations_on_account_delete
    BEFORE DELETE ON basejump.accounts
    FOR EACH ROW
    EXECUTE FUNCTION public.cleanup_sensitive_integrations_on_account_delete();

COMMIT;
