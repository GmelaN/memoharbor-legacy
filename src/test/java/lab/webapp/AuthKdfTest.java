package lab.webapp;

import java.nio.charset.StandardCharsets;
import org.apache.commons.codec.binary.Hex;
import org.junit.Test;
import static org.junit.Assert.*;

public class AuthKdfTest {
    @Test public void pbkdf2MatchesPublishedSha256Vectors() {
        assertEquals("120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b",
            Hex.encodeHexString(Auth.derive("password", "salt".getBytes(StandardCharsets.UTF_8), 1)));
        assertEquals("ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43",
            Hex.encodeHexString(Auth.derive("password", "salt".getBytes(StandardCharsets.UTF_8), 2)));
        assertEquals("c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a",
            Hex.encodeHexString(Auth.derive("password", "salt".getBytes(StandardCharsets.UTF_8), 4096)));
    }

    @Test public void retainsStandardBase64AndUrlSafeCsrfEncoding() {
        byte[] bytes = new byte[] {(byte) 251, (byte) 255};
        assertEquals("+/8=", org.apache.commons.codec.binary.Base64.encodeBase64String(bytes));
        assertEquals("-_8", org.apache.commons.codec.binary.Base64.encodeBase64URLSafeString(bytes));
    }

    @Test public void unicodePasswordsUseUtf8LikeTheOriginalProvider() {
        assertEquals("590db5f5214baa9ae55e5307c40b301111ebbce91e5b8ba04f2c69e145f10dfd",
            Hex.encodeHexString(Auth.derive("비밀번호123", "소금".getBytes(StandardCharsets.UTF_8), 4096)));
    }
}
