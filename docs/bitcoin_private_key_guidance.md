# Handling Leaked Cryptocurrency Private Keys

The project occasionally receives third-party data dumps that may include purported cryptocurrency private keys. Possessing or attempting to use private keys that belong to someone else can expose you to significant legal, ethical, and security risks. Treat any such material with extreme caution.

## Recommended Actions

1. **Do not attempt to import or use leaked keys.** Unauthorized access to wallets is illegal in most jurisdictions.
2. **Verify provenance.** If you unexpectedly encounter key data, assume it is untrusted and potentially malicious.
3. **Isolate sensitive inputs.** Use air-gapped analysis systems if you must examine suspicious datasets for defensive research.
4. **Report responsibly.** Notify the original data owner or relevant platform when feasible. Coordinate with legal counsel before disclosing sensitive findings publicly.
5. **Sanitize repositories.** Remove leaked keys or other secret material from version control history wherever possible. Document the sanitization process for auditability.

## Additional Resources

- [Bitcoin Optech - Key Management Best Practices](https://bitcoinops.org/en/topics/key-management/)
- [CNCERT/CC Incident Handling Guidelines](https://www.cert.org.cn/)
- [NIST SP 800-57 Part 1 Rev. 5: Key Management Guidelines](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

This guidance helps the team respond to unsolicited dumps securely while maintaining compliance with international regulations.
