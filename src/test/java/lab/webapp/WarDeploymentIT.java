package lab.webapp;

import java.io.File;
import java.net.HttpURLConnection;
import java.net.URL;
import org.apache.catalina.startup.Tomcat;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;

public class WarDeploymentIT {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    @Test public void packagedWarDiscoversServletAndEnforcesDescriptor() throws Exception {
        File war = new File("target/memoharbor.war");
        assertTrue("Package the WAR before running this integration test", war.isFile());
        Tomcat server = new Tomcat();
        server.setBaseDir(temporary.newFolder("server").getAbsolutePath());
        server.setPort(0);
        server.getConnector();
        server.setAddDefaultWebXmlToWebapp(false);
        server.addWebapp("/memoharbor", war.getAbsolutePath());
        String previous = System.getProperty("memoharbor.dataDir");
        System.setProperty("memoharbor.dataDir", temporary.newFolder("data").getAbsolutePath());
        try {
            server.start();
            int port = server.getConnector().getLocalPort();
            assertStatus(port, "/live", 200);
            assertStatus(port, "/health", 200);
            assertStatus(port, "/", 303);
            assertStatus(port, "/login", 200);
            assertStatus(port, "/.env", 403);
            assertStatus(port, "/WEB-INF/web.xml", 404);
        } finally {
            try { server.stop(); server.destroy(); }
            finally {
                if (previous == null) System.clearProperty("memoharbor.dataDir");
                else System.setProperty("memoharbor.dataDir", previous);
            }
        }
    }

    private void assertStatus(int port, String path, int expected) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/memoharbor" + path).openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(10000);
        try { assertEquals(path, expected, connection.getResponseCode()); }
        finally { connection.disconnect(); }
    }
}
