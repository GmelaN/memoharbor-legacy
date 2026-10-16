package lab.webapp;

import org.junit.Test;
import org.junit.Before;
import org.junit.Rule;
import org.junit.rules.TemporaryFolder;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.IOException;
import static org.junit.Assert.*;

public class DatabaseConfigTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();
    private Path root;
    @Before public void prepareDirectory() { root = temporary.getRoot().toPath(); }
    private void env(String content) throws Exception {
        Files.write(root.resolve(".env"), content.getBytes(StandardCharsets.UTF_8));
    }
    @Test public void rootEnvPreservesQuotedCredentialCharacters() throws Exception {
        env("\uFEFF# config\nexport DB_URL=jdbc:mariadb://db:3306/memoharbor\nDB_USER=apm\nDB_PASSWORD='sp ace#=한글'\n");
        DatabaseConfig c = DatabaseConfig.load(root, null);
        assertTrue(c.maria); assertEquals("sp ace#=한글", c.password);
        assertFalse(Files.exists(root.resolve("WEB-INF/db")));
    }
    @Test public void missingDefaultUsesSqliteButExplicitMissingFails() throws Exception {
        assertFalse(DatabaseConfig.load(root, null).maria);
        assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(root, root.resolve("missing.env").toString()); } });
    }
    @Test public void packedWarUsesPersistentWildFlyDataDirectory() throws Exception {
        Path serverData = root.resolve("server-data");
        DatabaseConfig c = DatabaseConfig.load(null, null, null, serverData.toString());
        assertFalse(c.maria);
        assertEquals("jdbc:sqlite:" + serverData.resolve("memoharbor/memoharbor.sqlite").toAbsolutePath(), c.url);
        assertTrue(Files.isDirectory(serverData.resolve("memoharbor")));
    }
    @Test public void explicitDataDirectoryOverridesWildFlyAndExplodedWar() throws Exception {
        Path data = root.resolve("external-data");
        DatabaseConfig c = DatabaseConfig.load(root, null, data.toString(), root.resolve("server-data").toString());
        assertEquals("jdbc:sqlite:" + data.resolve("memoharbor.sqlite").toAbsolutePath(), c.url);
        assertFalse(Files.exists(root.resolve("WEB-INF/db")));
        assertFalse(Files.exists(root.resolve("server-data")));
    }
    @Test public void packedWarCanUseExternalMariaDbConfiguration() throws Exception {
        env("DB_URL=jdbc:mariadb://db:3306/test\nDB_USER=user\nDB_PASSWORD=secret\n");
        assertTrue(DatabaseConfig.load(null, root.resolve(".env").toString(), null, null).maria);
        assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(null, root.resolve("missing.env").toString(), null, root.toString()); } });
        assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(null, null, null, null); } });
    }
    @Test public void invalidConfigNeverSilentlyFallsBackOrPrintsValues() throws Exception {
        env("DB_URL=jdbc:mariadb://db:3306/test\nDB_USER=user\n");
        assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(root, null); } });
        env("DB_URL=jdbc:h2:mem:test\nDB_USER=user\nDB_PASSWORD=secret\n");
        assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(root, null); } });
        env("DB_URL=jdbc:mariadb://db:3306/test\nDB_USER=user\nDB_PASSWORD=secret\nDB_PASSWORD=other\n");
        IOException error = assertThrows(IOException.class, new org.junit.function.ThrowingRunnable() { public void run() throws Throwable { DatabaseConfig.load(root, null); } });
        assertFalse(error.getMessage().contains("secret")); assertFalse(error.getMessage().contains("other"));
    }
}
