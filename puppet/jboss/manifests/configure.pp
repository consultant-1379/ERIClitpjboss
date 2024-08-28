define jboss::configure (
             $service_name,             # string
             $ensure
             ) {

    Exec { path => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ] }

    exec { "install-jdk":
        command => "yum install -y jdk",
        unless => "rpm -q jdk",
        timeout => 0,
        require => Yumrepo['3PP'],
    }

    # Install JBoss EAP which requires jdk to be installed
    exec { "install-jboss-eap":
        command => "yum install -y EXTRlitpjbosseap_CXP9031031",
        unless => "rpm -q EXTRlitpjbosseap_CXP9031031",
        timeout => 0,
        require => Exec['install-jdk'],
    }

    exec { "install-litp-jboss":
        command => "yum install -y ERIClitpmnjboss_CXP9030959",
        unless => "rpm -q ERIClitpmnjboss_CXP9030959",
        timeout => 0,
        require => Yumrepo['LITP'],
    }

    # Create a symlink which requires litp jboss to be installed
    file { "/etc/init.d/$service_name":
        ensure => 'link',
        target => '/opt/ericsson/nms/litp/bin/litp-jboss',
        require => Exec ['install-litp-jboss'],
    }
}
